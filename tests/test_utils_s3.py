import io
import json
import pytest
from services.utils import s3

BUCKET_NAME = "atd-knack-services"
FILENAME = "dev/test_record.json"
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
