"""Multi-threaded uploading of file-like objects to S3."""
from multiprocessing.dummy import Pool

import boto3


class RecordPackage:
    def __init__(self, *, fileobj, bucket_name, file_name):
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
    client = boto3.client("s3")
    return client.upload_fileobj(
        record_package.fileobj, record_package.bucket_name, record_package.file_name,
    )


def upload(record_packages, processes=8):
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

    return responses
