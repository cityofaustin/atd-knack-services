#!/usr/bin/env python

# docker run -it --rm --env-file env_file -v /Users/john/Dropbox/atd/atd-knack-services:/app atddocker/atd-knack-services:production services/records_to_socrata.py -a data-tracker -c object_11 -e prod
# python services/records_to_socrata.py -a data-tracker -c object_11 -e prod
import os

import knackpy

from config.knack import CONFIG
from config.s3 import BUCKET_NAME
import utils


def lower_case_keys(records):
    return [{key.lower(): val for key, val in record.items()} for record in records]


def bools_to_strings(records):
    for record in records:
        for k, v in record.items():
            if isinstance(v, bool):
                record[k] = str(v)
    return records


def patch_formatters(app, location_fields):
    """replace knackpy's default address fomatter with our custom socrata formatter"""
    for key in location_fields:
        for field_def in app.field_defs:
            if field_def.key == key:
                field_def.formatter = utils.socrata.socrata_formatter_location
                break
    return app


def main():
    args = utils.args.cli_args(["app-name", "container", "env", "date"])
    config = CONFIG.get(args.app_name).get(args.container)
    APP_ID = os.getenv("KNACK_APP_ID")
    metadata_fname = f"{args.env}/{args.app_name}/metadata.json"
    metadata = utils.s3.download_one(bucket_name=BUCKET_NAME, fname=metadata_fname)
    prefix = f"{args.env}/{args.app_name}/{args.container}"

    records_raw = utils.s3.download_many(
        bucket_name=BUCKET_NAME, prefix=prefix, date_filter=args.date, as_dicts=True
    )

    if not records_raw:
        return 0

    logger.info(f"{len(records_raw)} to process.")

    app = knackpy.App(app_id=APP_ID, metadata=metadata)
    location_fields = config.get("location_fields")

    if location_fields:
        app = patch_formatters(app, location_fields)

    app.data[args.container] = records_raw

    records = app.get(args.container)
    payload = [record.format() for record in records]
    payload = lower_case_keys(payload)
    payload = bools_to_strings(payload)
    resource_id = config["socrata_resource_id"]
    method = "upsert" if args.date else "replace"
    res = utils.socrata.publish(method=method, resource_id=resource_id, payload=payload)
    return res


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
