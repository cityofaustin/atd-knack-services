#!/usr/bin/env python
"""Download all records from S3 and *replace* destination layer in ArcGIS Online"""
import os

import arcgis
import arrow
import knackpy

import utils
from config.s3 import BUCKET_NAME
from config.knack import CONFIG

# docker run -it --rm --env-file env_file -v /Users/john/Dropbox/atd/atd-knack-services:/app atddocker/atd-knack-services:production services/records_to_agol.py -a data-tracker -c view_197 -e prod -d 2020-11-14
SPATIAL_REFERENCE = 4326
URL = "https://austin.maps.arcgis.com"
USERNAME = os.getenv("AGOL_USERNAME")
PASSWORD = os.getenv("AGOL_PASSWORD")
APP_ID = os.getenv("KNACK_APP_ID")


def main():
    args = utils.args.cli_args(["app-name", "container", "env"])
    config = CONFIG.get(args.app_name).get(args.container)
    upsert_matching_field = config["upsert_matching_field"]
    location_fields = config.get("location_fields")
    service_id = config["service_id"]
    layer_id = config["layer_id"]
    metadata_fname = f"{args.env}/{args.app_name}/metadata.json"
    metadata = utils.s3.download_one(bucket_name=BUCKET_NAME, fname=metadata_fname)
    prefix = f"{args.env}/{args.app_name}/{args.container}"

    records_raw = utils.s3.download_many(
        bucket_name=BUCKET_NAME, prefix=prefix, as_dicts=True
    )

    if not records_raw:
        return 0

    logger.info(f"{len(records_raw)} to process.")

    app = knackpy.App(app_id=APP_ID, metadata=metadata)
    app.data[args.container] = records_raw
    records = app.get(args.container)

    gis = arcgis.GIS(url=URL, username=USERNAME, password=PASSWORD)
    service = gis.content.get(service_id)
    layer = service.layers[layer_id]
    features = [
        utils.agol.build_feature(record, SPATIAL_REFERENCE, location_fields[0])
        for record in records
    ]


    """
    The arcgis package does have a method that supports upserting: append()
    https://developers.arcgis.com/python/api-reference/arcgis.features.toc.html#featurelayer  # noqa

    However this method errored out on multiple datasets and i gave up.
    layer.append(
        edits=features, upsert=True, upsert_matching_field="id"
    )
    """

    layer.manager.truncate()
    
    layer.edit_features(
        adds=features
    )
    



if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
