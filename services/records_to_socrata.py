#!/usr/bin/env python
import os

import arrow
import knackpy

from config.knack import CONFIG
import utils


def handle_floating_timestamps(records, floating_timestamp_fields):
    """Socrata's fixed timestamp dataType does not allow tz info :(
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


def get_boolean_columns(client_metadata):
    return [
        col["fieldName"]
        for col in client_metadata["columns"]
        # boolean fields in socrata are type "checkbox"
        if col["dataTypeName"] == "checkbox"
    ]


def bools_to_strings(records, boolean_columns):
    """Convert booleans from knack to strings
    Some Socrata datasets have been been created with type mismatch b/t Knack and Socrata,
    where a boolean field in Knack is configured as a text field in Socrata.
    This function converts a Knack boolean to a string.

    Args:
        records (list): a list of record dictionaries
        boolean_columns (_type_): the boolean columns in Socrata
    
    Returns:
        None: records are updated in-place
    """
    for record in records:
        for key, val in record.items():
            if isinstance(val, bool) and key not in boolean_columns:
                record[key] = str(val)


def handle_arrays(records):
    for record in records:
        for k, v in record.items():
            if isinstance(v, list):
                # assumes values in list can be coerced to to strings
                record[k] = ", ".join([str(i) for i in v])


def remove_unknown_fields(payload, client_metadata):
    """
    Modifies payload by removing the fields not found in Socrata
    Prevents "400 Client Error: Bad Request. Illegal field name sent" response
    :param payload: records payload to send to Socrata
    :param client_metadata: Socrata metadata for app
    """
    payload_field_names = payload[0].keys()
    column_names = [c["fieldName"] for c in client_metadata["columns"]]
    unknown_fields = [
        field_name
        for field_name in payload_field_names
        if field_name not in column_names
    ]
    if unknown_fields:
        logger.info(f"Record field names not in Socrata: {unknown_fields}")
        for record in payload:
            for unknown_field in unknown_fields:
                record.pop(unknown_field, None)


def find_field_def(field_defs, field_id):
    matched = [f for f in field_defs if f.key == field_id]
    try:
        return matched[0]
    except IndexError:
        raise ValueError(f"Unable to find fieldDef for {field_id}")


def patch_formatters(field_defs, location_field_id, metadata_socrata):
    """Replace knackpy's default address formatter with a custom socrata formatter for
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
    elif socrata_field_type == "multipoint":
        formatter_func = utils.knack.socrata_formatter_multipoint
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

    args = utils.args.cli_args(["app-name", "container", "date"])
    logger.info(args)

    container = args.container
    config = CONFIG.get(args.app_name).get(container)

    if not config:
        raise ValueError(
            f"No config entry found for app: {args.app_name}, container: {container}"
        )

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
        order_by="record_id",
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
    # format knack field names as lowercase/no spaces
    payload = [utils.shared.format_keys(record) for record in payload]
    # remove unknown fields first to reduce extra processing when doing subsequent transforms
    remove_unknown_fields(payload, metadata_socrata)
    boolean_columns = get_boolean_columns(metadata_socrata)
    bools_to_strings(payload, boolean_columns)
    handle_arrays(payload)
    floating_timestamp_fields = utils.socrata.get_floating_timestamp_fields(
        resource_id, metadata_socrata
    )
    handle_floating_timestamps(payload, floating_timestamp_fields)

    timestamp_key = config.get("append_timestamps_socrata", {}).get("key")

    if timestamp_key:
        utils.socrata.append_current_timestamp(payload, timestamp_key)

    method = "replace" if not args.date else "upsert"

    if config.get("no_replace_socrata") and method == "replace":
        raise ValueError(
            """
            Replacement of this Socrata dataset is not allowed. Specify a date range or
            modify the 'no_replace_socrata' setting in this container's config.
            """
        )

    utils.socrata.publish(
        method=method, resource_id=resource_id, payload=payload, client=client_socrata
    )
    logger.info(f"{len(payload)} records processed.")


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
