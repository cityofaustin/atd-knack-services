#!/usr/bin/env python
"""Download *all* records from PostgREST and *replace* destination layer in
ArcGIS Online"""
import os

import arcgis
import knackpy

import utils
from config.knack import CONFIG

SPATIAL_REFERENCE = 4326
URL = "https://austin.maps.arcgis.com"
USERNAME = os.getenv("AGOL_USERNAME")
PASSWORD = os.getenv("AGOL_PASSWORD")
APP_ID = os.getenv("KNACK_APP_ID")
PGREST_JWT = os.getenv("PGREST_JWT")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")


def main():
    args = utils.args.cli_args(["app-name", "container"])
    container = args.container
    config = CONFIG.get(args.app_name).get(container)
    location_field_id = config.get("location_field_id")
    service_id = config["service_id"]
    layer_id = config["layer_id"]
    item_type = config["item_type"]

    client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    metadata_knack = utils.postgrest.get_metadata(client_postgrest, APP_ID)
    app = knackpy.App(app_id=APP_ID, metadata=metadata_knack)

    logger.info(f"Downloading records from app {APP_ID}, container {container}.")

    data = client_postgrest.select(
        "knack",
        params={
            "select": "record",
            "app_id": f"eq.{APP_ID}",
            "container_id": f"eq.{container}",
        },
    )

    logger.info(f"{len(data)} to process.")

    if not data:
        return

    app.data[container] = [r["record"] for r in data]
    records = app.get(container)

    gis = arcgis.GIS(url=URL, username=USERNAME, password=PASSWORD)
    service = gis.content.get(service_id)

    if item_type == "layer":
        layer = service.layers[layer_id]
    elif item_type == "table":
        layer = service.tables[layer_id]
    else:
        raise ValueError(f"Unknown item_type specified: {item_type}")

    features = [
        utils.agol.build_feature(record, SPATIAL_REFERENCE, location_field_id)
        for record in records
    ]
    """
    The arcgis package does have a method that supports upserting: append()
    https://developers.arcgis.com/python/api-reference/arcgis.features.toc.html#featurelayer  # noqa E501

    However this method errored out on multiple datasets and i gave up.
    layer.append(
        edits=features, upsert=True, upsert_matching_field="id"
    )
    """
    layer.manager.truncate()
    layer.edit_features(adds=features)


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
