""" Download all files from a folder in an S3 bucket """
import json
from multiprocessing.dummy import Pool

import arrow
import boto3


def get_obj_data(obj):
    return obj.get()["Body"].read().decode()


def filter_by_date(objs, date):
    compare_date = arrow.get(date)
    return [obj for obj in objs if arrow.get(obj.last_modified) >= compare_date]


def download(bucket_name, prefix, date_filter=None, as_dicts=True, processes=8):
    """
    Args:
        bucket_name (str): The S3 bucket name from which files will be downloaded
        prefix (str): The bucket subfolder from which files will be downloaded
        date_filter (int): Optional unix timestamp which will be used to include only
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
