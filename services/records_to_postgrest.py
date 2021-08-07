#!/usr/bin/env python

""" Download Knack records and upload to Postgres(t) """
from multiprocessing.dummy import Pool
import os

import knackpy

from config.knack import CONFIG, APP_TIMEZONE
import utils


def build_payload(
    records, app_id, container,
):
    payload = []
    for record in records:
        payload.append(
            {
                "record_id": record["id"],
                "app_id": app_id,
                "container_id": container,
                "record": record,
            }
        )
    return payload


def container_kwargs(container, config, obj=None, scene=None, view=None):
    """Return the object key or find the scene key and return it with the view key"""
    if "object_" in container:
        obj = container
    else:
        scene = config.get("scene")
        view = container

    return {"obj": obj, "scene": scene, "view": view}


def chunk_payload(client, data, chunk_size):
    def chunks(data, chunk_size):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    return [{"client": client, "payload": chunk} for chunk in chunks(data, chunk_size)]


def upsert_wrapper(data):
    return data["client"].upsert("knack", data["payload"])


def main():
    CHUNK_SIZE = 200
    APP_ID = os.getenv("KNACK_APP_ID")
    API_KEY = os.getenv("KNACK_API_KEY")
    PGREST_JWT = os.getenv("PGREST_JWT")
    PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")

    args = utils.args.cli_args(["app-name", "container", "date"])
    logger.info(args)
    container = args.container
    app_config = CONFIG.get(args.app_name).get(container)

    if not app_config:
        raise ValueError(
            f"No config entry found for app: {args.app_name}, container: {container}"
        )

    modified_date_field = app_config.get("modified_date_field")

    filters = utils.knack.date_filter_on_or_after(
        args.date, modified_date_field, tzinfo=APP_TIMEZONE
    )

    logger.info("Downloading records from Knack...")

    kwargs = container_kwargs(container, app_config)

    records = knackpy.api.get(
        app_id=APP_ID, api_key=API_KEY, filters=filters, **kwargs,
    )

    logger.info(f"{len(records)} to process.")

    if not records:
        return

    payload = build_payload(records, APP_ID, container)

    client = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)

    if not args.date:
        # if no date is provided, we do a full a replace of the data
        client.delete(
            "knack",
            params={"container_id": f"eq.{container}", "app_id": f"eq.{APP_ID}"},
        )

    chunked_payload = chunk_payload(client, payload, CHUNK_SIZE)

    with Pool(processes=4) as pool:
        """
        Increasing the number of processes (actually, threads because that's what a
        dummy pool does), can definitely improve performance, but postgrest was
        dropping connections pretty frequently under heavy loads. TODO: revisit
        this when we have a production deployment with more compute. There is a TBD
        sweet spot of chunk size vs # of threads.
        """
        pool.map(upsert_wrapper, chunked_payload)

    logger.info(f"Records uploaded: {len(records)}")

    return


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
