""" Multi-threaded uploading/downloading to/from AWS S3"""
import json
from multiprocessing.dummy import Pool

import arrow
import boto3


def handle_results(results):
    # TODO
    return results


def get_obj_data(obj):
    return obj.get()["Body"].read().decode()


def filter_by_date(objs, date):
    compare_date = arrow.get(date)
    return [obj for obj in objs if arrow.get(obj.last_modified) >= compare_date]


def download_many(*, bucket_name, prefix, date_filter=None, as_dicts=True, processes=8):
    """ Multi-threaded downloading of files from a folder in an S3 bucket.

    Args:
        bucket_name (str): The S3 bucket name from which files will be downloaded
        prefix (str): The bucket subdirectory from which files will be downloaded
        date_filter (int): Optional posix timestamp which will be used to include only
            those files have been modified on or after the given date.
        as_dicts (bool, optional): If the files should be returned as a list of
            dictionaries. If true, assumes file contents are json. Defaults to True.
        processes (int): The number of concurrent threads to use for downloading.
            Defaults to 8.

    Returns:
        list: Of dictionaries (if as_dict==True) or decoded file contents.
    """
    s3 = boto3.resource("s3")

    bucket = s3.Bucket(bucket_name)

    objs_all = bucket.objects.filter(Prefix=prefix)

    objs_to_download = (
        filter_by_date(objs_all, date_filter) if date_filter else objs_all
    )

    with Pool(processes=processes) as pool:
        objs = pool.map(get_obj_data, objs_to_download)

    return [json.loads(obj) for obj in objs] if as_dicts else objs


def download_one(*, bucket_name, fname, as_dict=True):
    """Download a single file object from S3.

    Args:
        bucket_name (str): The host bucket name
        fname (str): The file to be downloaded
        as_dict (bool, optional): If the file should be returned a dict. If true,
            assumes file contents are json. Defaults to True.

    Returns:
        dict if as_dict==True else the decoded file content
    """
    s3 = boto3.resource("s3")
    obj = s3.Object(bucket_name, fname)
    data = get_obj_data(obj)
    # TODO: handle errors/no data
    return json.loads(data) if as_dict else data


class RecordPackage:
    def __init__(self, *, fileobj: bytes, bucket_name: str, file_name: str):
        """A simple container for holding data to be processed by boto3 via
        multiprocessing.dummy.Pool.

        Args:
            fileobj (bytes-like object): The bytes-like file object to be uploaded. This
                would typically be either a _io.BytesIO class or a _io.BufferedReader.
            bucket_name (str): the name of the destination S3 bucket.
            file_name (str): the full path to the file in the S3 bucket. e.g.,
                "object_11/xyz.json".
        """
        self.fileobj = fileobj
        self.bucket_name = bucket_name
        self.file_name = file_name

    def __repr__(self):
        return f"<RecordPackage '{self.bucket_name}/{self.file_name}'>"


def _upload(record_package):
    session = boto3.session.Session()
    client = session.client("s3")
    return client.upload_fileobj(
        record_package.fileobj, record_package.bucket_name, record_package.file_name,
    )


def upload(record_packages: list, processes: int = 8):
    """ boto3 wrapper to upload files to S3 via multithreading.

    Args:
        - record_packages (list): A list of RecordPackage class instances.
    """
    with Pool(processes=processes) as pool:
        # be aware that the pool uses multiple threads, not processes. which is fine
        # for our purpose of making concurrent API calls
        responses = pool.map(_upload, record_packages)

    # todo: handle responses. each should be None. otherwise it's an error?
    # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/error-handling.html
    handle_results(responses)
    return responses
