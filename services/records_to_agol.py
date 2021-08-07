#!/usr/bin/env python
"""Download records from PostgREST and upsert to destination layer in ArcGIS Online"""
import os
import time

import arcgis
import arrow
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
MAX_RETRIES = 3


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def resilient_layer_request(func, args, max_retries=MAX_RETRIES):
    """
    An ArcGIS request wrapper to enable re-trying. The wrapper will only suppress timeout
    exceptions from the Rest API. Our separate response handler utility catches API
    errors.
    """
    attempts = 0
    while True:
        attempts += 1
        try:
            return func(**args)
        except Exception as e:
            """
            The ArcGIS Python API raises a generic Exception class on timeout, so we parse the
            Exception content to be sure we pass the right case. The timeout message string
            we want to ignore:
                `Exception: Your request has timed out.`
            """
            if "timed out" not in e.__str__().lower() or attempts == max_retries:
                raise e
            logger.info(
                f"Retrying timed-out request on attempt #{attempts} of {max_retries}"
            )
            pass


def main():
    args = utils.args.cli_args(["app-name", "container", "date"])
    logger.info(args)
    container = args.container
    config = CONFIG.get(args.app_name).get(container)

    if not config:
        raise ValueError(
            f"No config entry found for app: {args.app_name}, container: {container}"
        )

    location_field_id = config.get("location_field_id")
    service_id = config["service_id"]
    layer_id = config["layer_id"]
    item_type = config["item_type"]

    client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    metadata_knack = utils.postgrest.get_metadata(client_postgrest, APP_ID)
    app = knackpy.App(app_id=APP_ID, metadata=metadata_knack)

    logger.info(f"Downloading records from app {APP_ID}, container {container}.")

    filter_iso_date_str = format_filter_date(args.date)

    data = client_postgrest.select(
        "knack",
        params={
            "select": "record",
            "app_id": f"eq.{APP_ID}",
            "container_id": f"eq.{container}",
            "updated_at": f"gte.{filter_iso_date_str}",
        },
        order_by="record_id",
    )

    logger.info(f"{len(data)} to process.")

    if not data:
        return

    app.data[container] = [r["record"] for r in data]
    records = app.get(container)

    fields_names_to_sanitize = [
        f.name
        for f in app.field_defs
        if f.type in ["short_text", "paragraph_text"]
        and (f.obj == container or container in f.views)
    ]

    gis = arcgis.GIS(url=URL, username=USERNAME, password=PASSWORD)
    service = gis.content.get(service_id)

    if item_type == "layer":
        layer = service.layers[layer_id]
    elif item_type == "table":
        layer = service.tables[layer_id]
    else:
        raise ValueError(f"Unknown item_type specified: {item_type}")

    logger.info("Building features...")

    features = [
        utils.agol.build_feature(
            record, SPATIAL_REFERENCE, location_field_id, fields_names_to_sanitize
        )
        for record in records
    ]

    if not args.date:
        """
        Completely replace destination data. arcgis does have layer.manager.truncate()
        method, but this method is not supported on the parent layer of parent-child
        relationships. So we truncate the layer by deleteing with a "where 1=1"
        expression. We use the "future" option to avoid request timeouts on large
        datasets.
        """
        logger.info("Deleting all features...")
        res = resilient_layer_request(
            layer.delete_features, {"where": "1=1", "future": True}
        )
        # returns a "<Future>" response class which does not appear to be documented
        while res._state != "FINISHED":
            logger.info(f"Response state: {res._state}. Sleeping for 1 second")
            time.sleep(1)
        utils.agol.handle_response(res._result)

    else:
        """
        Simulate an upsert by deleting features from AGOL if they exist.

        The arcgis package does have a method that supports upserting: append()
        https://developers.arcgis.com/python/api-reference/arcgis.features.toc.html#featurelayer  # noqa E501

        However this method errored out on multiple datasets and i gave up.
        layer.append(
            edits=features, upsert=True, upsert_matching_field="id"
        )
        """
        logger.info(f"Deleting {len(features)} features...")
        key = "id"
        keys = [f'\'{f["attributes"][key]}\'' for f in features]
        for key_chunk in chunks(keys, 100):
            key_list_stringified = ",".join(key_chunk)
            res = resilient_layer_request(
                layer.delete_features, {"where": f"{key} in ({key_list_stringified})"}
            )
            utils.agol.handle_response(res)

    logger.info("Uploading features...")

    for features_chunk in chunks(features, 500):
        logger.info("Uploading chunk...")
        res = resilient_layer_request(
            layer.edit_features, {"adds": features_chunk, "rollback_on_failure": False}
        )
        utils.agol.handle_response(res)


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
