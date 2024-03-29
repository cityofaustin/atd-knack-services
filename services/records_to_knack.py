#!/usr/bin/env python
""" Fetch Knack records from Postgres(t) and upload to another Knack app """
import os
import arrow
import knackpy

from config.knack import CONFIG
from config.field_maps import FIELD_MAPS
import utils


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def get_pks(field_map, app_name_dest):
    """return the src and destination field name of the primary key"""
    pk_field = [f for f in field_map if f.get("primary_key")]
    try:
        assert len(pk_field) == 1
    except AssertionError:
        raise ValueError(
            "One (and only one) primary key is required. There's an error in the field map configuration."  # noqa E501
        )
    return pk_field[0]["src"], pk_field[0][app_name_dest]


def create_mapped_record(record, field_map, app_name_dest):
    """Map the data from the source Knack app to the destination app schema"""
    mapped_record = {}
    for field in field_map:
        field_src = field["src"]
        if field_src:
            """Note that a default value in the field map *never* overrides a value in
            the src data unless the src field ID is None"""
            val = record.get(field_src)
        else:
            try:
                val = field["default"]
            except KeyError:
                raise ValueError(
                    "A default default is required when source field is None"
                )

        field_dest = field[app_name_dest]
        handler_func = field.get("handler")
        mapped_record[field_dest] = val if not handler_func else handler_func(val)

    return mapped_record


def is_equal(rec_src, rec_dest, keys):
    tests = [rec_src[key] == rec_dest[key] for key in keys]
    return all(tests)


def remove_raw_tags(records):
    """
    Removes "_raw" from field names so special compound datatypes such as Persons or Emails can be
    left in their original format and then passed on to the destination Knack app.
    """
    fields_to_rename = [f for f in list(records[0].keys()) if "_raw" in f]
    if fields_to_rename:
        for rec in records:
            for f in fields_to_rename:
                rec[f.replace("_raw", "")] = rec.pop(f)
    return records


def handle_records(data_src, data_dest, field_map, app_name_dest):
    """
    data_src: list of records from source knack app
    data_dest: list of records in destination knack app
    field_map: list of objects containing source app fields mapped to destination app fields
    app_name_dest: name of destination knack app
    """
    pk_src, pk_dest = get_pks(field_map, app_name_dest)
    # make list of fields in records to compare for differences
    compare_keys = [
        field[app_name_dest] for field in field_map if not field.get("ignore_diff")
    ]
    todos = []
    for rec_src in data_src:
        matched = False
        # mapped record is record from source app with fields that match the destination app
        mapped_record = create_mapped_record(rec_src, field_map, app_name_dest)
        id_src = mapped_record[pk_dest]
        for rec_dest in data_dest:
            id_dest = rec_dest[pk_dest]
            if id_src == id_dest:
                matched = True
                if not is_equal(mapped_record, rec_dest, compare_keys):
                    mapped_record["id"] = rec_dest["id"]
                    todos.append(mapped_record)
                break
        if not matched:
            todos.append(mapped_record)
    todos = remove_raw_tags(todos)
    return todos


def main():
    APP_ID_SRC = os.getenv("KNACK_APP_ID_SRC")
    APP_ID_DEST = os.getenv("KNACK_APP_ID_DEST")
    API_KEY_DEST = os.getenv("KNACK_API_KEY_DEST")
    PGREST_JWT = os.getenv("PGREST_JWT")
    PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")

    args = utils.args.cli_args(["app-name", "container", "date", "app-name-dest"])
    logger.info(args)
    app_name_src = args.app_name
    app_name_dest = args.app_name_dest

    container_src = args.container
    config = CONFIG.get(app_name_src).get(container_src)
    container_dest = config.get("dest_apps").get(app_name_dest).get("container")
    object_dest = config.get("dest_apps").get(app_name_dest).get("object")
    client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    filter_iso_date_str = format_filter_date(args.date)

    logger.info(
        f"Downloading records from app {APP_ID_SRC} ({app_name_src}), container {container_src}."
    )

    data_src = client_postgrest.select(
        "knack",
        params={
            "select": "record",
            "app_id": f"eq.{APP_ID_SRC}",
            "container_id": f"eq.{container_src}",
            "updated_at": f"gte.{filter_iso_date_str}",
        },
        order_by="id",
    )

    logger.info(f"{len(data_src)} records to process")

    if not data_src:
        return

    logger.info(
        f"Updating/creating records in app {APP_ID_DEST} ({app_name_dest}), container {container_dest}."
    )

    # existing data in destination knack app
    data_dest = client_postgrest.select(
        "knack",
        params={
            "select": "record",
            "app_id": f"eq.{APP_ID_DEST}",
            "container_id": f"eq.{container_dest}",
        },
        order_by="id",
    )

    data_src = [r["record"] for r in data_src]
    data_dest = [r["record"] for r in data_dest]
    field_map = FIELD_MAPS.get(app_name_src).get(container_src)

    # identify new/changed records and map to destination Knack app schema
    todos = handle_records(data_src, data_dest, field_map, app_name_dest)

    logger.info(f"Updating/creating {len(todos)} records in the destination app.")

    if not todos:
        return

    count = 0
    for record in todos:
        if count % 10 == 0:
            logger.info(f"Uploading record {count} of {len(todos)}")
        method = "create" if not record.get("id") else "update"
        knackpy.api.record(
            app_id=APP_ID_DEST,
            api_key=API_KEY_DEST,
            obj=object_dest,
            method=method,
            data=record,
        )
        count += 1


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
