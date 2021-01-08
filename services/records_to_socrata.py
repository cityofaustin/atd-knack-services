#!/usr/bin/env python
import os

import arrow
import knackpy

from config.knack import CONFIG
import utils

def handle_floating_timestamps(records, floating_timestamp_fields):
    """ Socrata's fixed timestamp dataType does not allow tz info :(
        (Alternatively, one could setup a transform in Socrata to convert the datatype
        to a fixed timestamp:
        https://dev.socrata.com/docs/transforms/to_fixed_timestamp.html)
    """
    for record in records:
        for field in floating_timestamp_fields:
            dt = record.get(field)
            if not dt:
                continue
            record[field] = arrow.get(dt).format("YYYY-MM-DDTHH:mm:ss")
    return records


def format_keys(records):
    """ This script assumes that the source knack records' field labels map exactly
    to the socrata API column names, given that they are converted to lower case and
    spaces are replaced with underscores."""
    return [{key.lower().replace(" ", "_"): val for key, val in record.items()} for record in records]


def bools_to_strings(records):
    for record in records:
        for k, v in record.items():
            if isinstance(v, bool):
                record[k] = str(v)
    return records


def find_field_def(field_defs, field_id):
    matched = [f for f in field_defs if f.key == field_id]
    try:
        return matched[0]
    except IndexError:
        raise ValueError(f"Unable to find fieldDef for {field_id}")


def patch_formatters(field_defs, location_field_id, metadata_socrata):
    """Replace knackpy's default address fomatter with a custom socrata formatter for
    either `point` or `location` field types. `location` types are a legacy field
    type, so we have to munge the socrata metadata to determine which type(s) our
    dataset uses."""
    knackpy_field_def = find_field_def(field_defs, location_field_id)
    field_name_knack = knackpy_field_def.name
    socrata_field_type = utils.socrata.get_field_type_by_field_name(
        field_name_knack.lower(), metadata_socrata
    )
    if socrata_field_type == "point":
        formatter_func = utils.knack.socrata_formatter_point
    elif socrata_field_type == "location":
        formatter_func = utils.knack.socrata_formatter_location
    else:
        raise ValueError(
            f"Socrata data type for {location_field_id} ({field_name_knack}) is not a `point` or `location` type"  # noqa:E501
        )
    knackpy_field_def.formatter = formatter_func


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def main():
    APP_ID = os.getenv("KNACK_APP_ID")
    PGREST_JWT = os.getenv("PGREST_JWT")
    PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")

    args = utils.args.cli_args(["app-name", "container", "env", "date"])
    logger.info(args)

    container = args.container
    config = CONFIG.get(args.app_name).get(container)

    location_field_id = config.get("location_field_id")
    client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    metadata_knack = utils.postgrest.get_metadata(client_postgrest, APP_ID)
    app = knackpy.App(app_id=APP_ID, metadata=metadata_knack)
    filter_iso_date_str = format_filter_date(args.date)

    logger.info(f"Downloading records from app {APP_ID}, container {container}.")

    data = client_postgrest.select(
        "knack",
        params={
            "select": "record",
            "app_id": f"eq.{APP_ID}",
            "container_id": f"eq.{container}",
            "updated_at": f"gte.{filter_iso_date_str}",
        },
    )

    logger.info(f"{len(data)} records to process")

    if not data:
        return

    client_socrata = utils.socrata.get_client()
    resource_id = config["socrata_resource_id"]
    metadata_socrata = client_socrata.get_metadata(resource_id)

    if location_field_id:
        patch_formatters(app.field_defs, location_field_id, metadata_socrata)

    # side-load knack data so we can utilize knackpy Record class for formatting
    app.data[container] = [r["record"] for r in data]

    records = app.get(container)

    # apply transforms to meet socrata's expectations
    payload = [record.format() for record in records]
    payload = format_keys(payload)
    bools_to_strings(payload)
    floating_timestamp_fields = utils.socrata.get_floating_timestamp_fields(
        resource_id, metadata_socrata
    )
    handle_floating_timestamps(payload, floating_timestamp_fields)

    method = "upsert" if args.date else "replace"

    utils.socrata.publish(
        method=method, resource_id=resource_id, payload=payload, client=client_socrata
    )
    logger.info(f"{len(payload)} records processed.")


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
