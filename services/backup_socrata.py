import argparse
import datetime
import os
import requests

import boto3

from config.knack import CONFIG
import utils

BUCKET = os.getenv("BUCKET")
AWS_ACCESS_ID = os.getenv("AWS_ACCESS_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")


def export_dataset(resource_id):
    url = f"https://data.austintexas.gov/resource/{resource_id}.csv?$limit=99999999&$$app_token={SOCRATA_APP_TOKEN}"
    res = requests.get(url)
    if res.status_code != 200:
        raise res.text
    data = res.text
    return data


def main(args):
    aws_s3_client = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )

    # Parse Arguments
    app_name = args.app_name
    container = args.container
    resource_id = CONFIG[app_name][container]["socrata_resource_id"]
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

    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
