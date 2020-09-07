#!/usr/bin/env python

""" Download Knack records and upload to S3 """
import argparse
import io
import json
import logging
import os
import sys

import arrow
import knackpy

from config.knack import CONFIG
from config.s3 import BUCKET_NAME
import utils

# e.g. python knack_to_s3.py -c object_11 -d 0 -e prod
def fileobj(record):
    return io.BytesIO(json.dumps(record).encode())


def build_record_packages(records, bucket_name, app_name, env, container):
    return [
        utils.s3.RecordPackage(
            fileobj=fileobj(record),
            bucket_name=bucket_name,
            file_name=f"{env}/{app_name}/{container}/{record['id']}.json",
        )
        for record in records
    ]


def container_kwargs(container, config, obj=None, scene=None, view=None):
    """Knack API requires either an object key or a scene and view key"""
    if "object_" in container:
        obj = container
    else:
        scene = config.get("scene")
        view = container

    return {"obj": obj, "scene": scene, "view": view}


def main():
    args = utils.args.cli_args(["app-name", "container", "env", "date"])
    logging.info(args)

    utils.knack.set_env(args.app_name, args.env)
    app_id = os.getenv("app_id")
    api_key = os.getenv("api_key")
    config = CONFIG.get(args.app_name).get(args.container)

    if not config:
        raise ValueError(f"No config entry found for {args.app_name}, {args.container}")

    modified_date_field = config["modified_date_field"]
    filters = utils.knack.date_filter_on_or_after(args.date, modified_date_field)
    
    logging.info(filters)

    kwargs = container_kwargs(args.container, config)

    records = knackpy.api.get(
        app_id=app_id, api_key=api_key, filters=filters, **kwargs,
    )

    if not records:
        logging.info("No records to process.")
        return

    record_packages = build_record_packages(
        records, BUCKET_NAME, args.app_name, args.env, args.container
    )

    utils.s3.upload(record_packages)

    logging.info(f"Records uploaded: {len(record_packages)}")
    return


if __name__ == "__main__":
    # airflow needs this to see logs from the DockerOperator
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main()
