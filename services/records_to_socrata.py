#!/usr/bin/env python

import argparse
import json
import os

import knackpy
import sodapy

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
                field_def.formatter = utils.socrata.socrata_formatter
                break
    return app


def main():
    args = utils.args.cli_args(["app-name", "container", "env", "date"])
    config = CONFIG.get(args.app_name).get(args.container)
    utils.knack.set_env(args.app_name, args.env)
    app_id = os.getenv("app_id")
    metadata_fname = f"{args.env}/{args.app_name}/metadata.json"
    metadata = utils.s3.download_one(bucket_name=BUCKET_NAME, fname=metadata_fname)
    prefix = f"{args.env}/{args.app_name}/{args.container}"

    records_raw = utils.s3.download_many(
        bucket_name=BUCKET_NAME, prefix=prefix, date_filter=args.date, as_dicts=True
    )

    if not records_raw:
        return 0

    app = knackpy.App(app_id=app_id, metadata=metadata)
    location_fields = config.get("location_fields")

    if location_fields:
        app = patch_formatters(app, location_fields)

    app.data[args.container] = records_raw

    records = app.get(args.container)
    payload = [record.format() for record in records]
    payload = lower_case_keys(payload)
    payload = bools_to_strings(payload)
    resource_id = config.get("socrata_resource_id")
    res = utils.socrata.upsert(resource_id=resource_id, payload=payload)
    # TODO: handle response
    return res


if __name__ == "__main__":
    main()
