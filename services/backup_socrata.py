#!/usr/bin/env python
import argparse
import csv
import datetime
from io import StringIO
import json
import os
import requests
from requests.auth import HTTPBasicAuth

import boto3

from config.knack import CONFIG
import utils

BUCKET = os.getenv("BUCKET")
AWS_ACCESS_ID = os.getenv("AWS_ACCESS_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")


def export_dataset(resource_id):
    basic = HTTPBasicAuth(username=SOCRATA_API_KEY_ID, password=SOCRATA_API_KEY_SECRET)
    keep_going = True
    offset = 0
    data = []
    while keep_going:
        url = f"https://datahub.austintexas.gov/resource/{resource_id}.json?$limit=100000&$offset={offset}&$$app_token={SOCRATA_APP_TOKEN}"
        res = requests.get(url, auth=basic, timeout=30)
        if res.status_code != 200:
            raise Exception(res.text)
        offset += 100000
        if not json.loads(res.text):
            keep_going = False
        else:
            data = data + json.loads(res.text)

    # Get column headers
    url = f"https://datahub.austintexas.gov/resource/{resource_id}.csv?$limit=0&$$app_token={SOCRATA_APP_TOKEN}"
    res = requests.get(url, auth=basic, timeout=30)
    csv_file = StringIO(res.text)
    csv_reader = csv.reader(csv_file)
    for row in csv_reader:
        headers = row

    # Output to csv
    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=headers)
    csv_writer.writeheader()
    csv_writer.writerows(data)
    return csv_data.getvalue()

def main(args):
    aws_s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    # Parse Arguments
    if args.app_name and args.container:
        app_name = args.app_name
        container = args.container
        resource_id = CONFIG[app_name][container]["socrata_resource_id"]
    elif args.dataset:
        resource_id = args.dataset
    else:
        raise Exception("No Socrata resource argument supplied.")
    logger.info(resource_id)

    # File name and get s3 folder
    subdir = resource_id.replace("-", "_")  # folder name is resource ID
    timestamp = datetime.datetime.now()
    file_name = timestamp.strftime("%y_%m_%d")
    file_name = f"{subdir}/{file_name}.csv"

    # Get data from Socrata
    body = export_dataset(resource_id)

    # Upload CSV to s3
    aws_s3_client.put_object(Body=body, Bucket=BUCKET, Key=file_name)
    logger.info(f"created backup file: {file_name}")

    # Keeping only the last 30 days of data
    s3_file_list = aws_s3_client.list_objects_v2(Bucket=BUCKET, Prefix=subdir)[
        "Contents"
    ]
    if len(s3_file_list) > 30:
        get_last_modified = lambda obj: int(obj["LastModified"].strftime("%s"))
        oldest_file = [
            obj["Key"] for obj in sorted(s3_file_list, key=get_last_modified)
        ][0]
        aws_s3_client.delete_object(Bucket=BUCKET, Key=oldest_file)
        logger.info(f"deleted backup file: {oldest_file}")


if __name__ == "__main__":
    # CLI arguments definition
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--app-name",
        type=str,
        help="str: Name of the Knack App in knack.py config file",
    )

    parser.add_argument(
        "-c",
        "--container",
        type=str,
        help="str: AKA API view in the config.py file with the selected socrata_resource_id to backup.",
    )

    parser.add_argument(
        "-f",
        "--dataset",
        type=str,
        help="str: Alternatively to app name/container, the Socrata resource ID (AKA 4x4).",
    )

    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
