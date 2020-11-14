#!/usr/bin/env python

""" Download Knack records and upload to S3 """
import io
import json
import os

import knackpy

from config.knack import CONFIG, APP_TIMEZONE
from config.s3 import BUCKET_NAME
import utils


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
    logger.info(args)

    APP_ID = os.getenv("KNACK_APP_ID")
    API_KEY = os.getenv("KNACK_API_KEY")
    config = CONFIG.get(args.app_name).get(args.container)

    if not config:
        raise ValueError(f"No config entry found for {args.app_name}, {args.container}")

    modified_date_field = config["modified_date_field"]

    filters = utils.knack.date_filter_on_or_after(
        args.date, modified_date_field, tzinfo=APP_TIMEZONE
    )

    kwargs = container_kwargs(args.container, config)
    logger.info(f"Downloading records from Knack...")
    records = knackpy.api.get(
        app_id=APP_ID, api_key=API_KEY, filters=filters, **kwargs,
    )

    if not records:
        logger.info("No records to process.")
        return
    
    logger.info(f"{len(records)} to process.")

    record_packages = build_record_packages(
        records, BUCKET_NAME, args.app_name, args.env, args.container
    )
    logger.info("Uploading records to S3...")
    utils.s3.upload(record_packages)

    logger.info(f"Records uploaded: {len(record_packages)}")
    return


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
