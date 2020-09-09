import io
import json
import os

import arrow
import boto3
import pytest
from services.utils import s3

BUCKET_NAME = "atd-knack-services"
PREFIX = "dev/_tests"
FILENAME = os.path.join(PREFIX, "test_record.json")
APP_NAME = "tests"


@pytest.fixture
def record_data():
    return {"fake": "fake"}


@pytest.fixture
def fileobj(record_data):
    return io.BytesIO(json.dumps(record_data).encode())


@pytest.fixture
def record_package(fileobj):
    return s3.RecordPackage(
        fileobj=fileobj, bucket_name=BUCKET_NAME, file_name=FILENAME
    )


def test_record_package_success(record_package):
    assert record_package.__repr__()


def test_upload(record_package):
    results = s3.upload([record_package])
    # results should = [None]
    assert not any(results)


def test_download_one(record_data):
    data = s3.download_one(bucket_name=BUCKET_NAME, fname=FILENAME)
    assert data == record_data


def test_download_many(record_data):
    data = s3.download_many(bucket_name=BUCKET_NAME, prefix=PREFIX)
    assert data[0] == record_data


def test_filter_by_date_future(record_data):
    """Query S3 for records modified 1 hour from now"""
    resource = boto3.resource("s3")
    bucket = resource.Bucket(BUCKET_NAME)
    objs_all = bucket.objects.filter(Prefix=PREFIX)
    now = arrow.now().shift(hours=1).format()
    filtered_objs = s3.filter_by_date(objs_all, now)
    assert len(filtered_objs) == 0


def filter_by_date_past(record_data):
    """Query S3 for records modified 1 hour ago"""
    resource = boto3.resource("s3")
    bucket = resource.Bucket(BUCKET_NAME)
    objs_all = bucket.objects.filter(Prefix=PREFIX)
    now = arrow.now().shift(hours=-1).format()
    filtered_objs = s3.filter_by_date(objs_all, now)
    assert len(filtered_objs) == 1
