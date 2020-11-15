#!/usr/bin/env python
"""Upload knack metadata to S3. metadata is deposited at
's3://{bucket-name}/{env}/{app_name}/metadata.json'
"""
import io
import json
import os

import boto3
import knackpy

from config.s3 import BUCKET_NAME
import utils


def main():
    args = utils.args.cli_args(["app-name", "env"])
    APP_ID = os.getenv("KNACK_APP_ID")
    metadata = knackpy.api.get_metadata(app_id=APP_ID)
    payload = json.dumps(metadata).encode()
    client = boto3.client("s3")

    with io.BytesIO(payload) as f:
        response = client.upload_fileobj(
            f, f"{BUCKET_NAME}", f"{args.env}/{args.app_name}/metadata.json",
        )

    if response:
        # todo: understand s3 error responses
        raise Exception("Unknown error.")

    return response


if __name__ == "__main__":
    main()
