#!/usr/bin/env python

""" upload knack metadata to S3. metadata is deposited at
's3://{bucket-name}/{app_name}-{env}/{app_id}.json'
"""
import argparse
import io
import json
import os

import boto3
import knackpy

from config.s3 import BUCKET_NAME
import utils


def main():
    args = utils.args.cli_args(["app-name", "env"])
    utils.knack.set_env(args.app_name, args.env)
    app_id = os.getenv("app_id")
    metadata = knackpy.api.get_metadata(app_id=app_id)
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
