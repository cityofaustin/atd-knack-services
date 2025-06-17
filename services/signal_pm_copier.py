#!/usr/bin/env python
"""
Copy traffic signal preventative maintenance (PM) records for the primary signal to secondary signal(s)
"""
import argparse
from datetime import date
import os

import knackpy

from config.knack import CONFIG
import utils

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")


def generate_field_name_lookup(record):
    lookup = {}
    for field in record.field_defs:
        lookup[field.key] = field.name
    return lookup


def find_knack_field_name(field_name, field_map):
    """
    Returns the knack field name for a given column name
    """
    for field in field_map:
        if field_map[field] == field_name:
            return field
    raise Exception("Field name not found in field map.")


def record_to_knack(record, object_id, method):
    if method == "update":
        assert "id" in record
    res = knackpy.api.record(
        app_id=APP_ID,
        api_key=API_KEY,
        obj=object_id,
        method=method,
        data=record,
    )
    return res


def main(args):
    # Parse Arguments
    app_name = args.app_name
    container = args.container
    logger.info(args)

    # Selecting correct config for the view
    config = CONFIG[app_name][container]
    app = knackpy.App(app_id=APP_ID, api_key=API_KEY)

    # 1. Check for work orders to be copied.
    # Note that this view is already pre-filtered in Knack to PM records that need to be copied.
    pm_records = app.get(container)
    if not pm_records:
        logger.info("No PM records need to be copied, did nothing.")
        return 0
    pm_field_names = generate_field_name_lookup(pm_records[0])
    logger.info(f"{len(pm_records)} PM records to be copied.")

    # 2. Download primary signal -> secondary signal relationships
    secondary_key = config["secondary_signals_field"]

    # Filtering out traffic signals without secondary signals
    filters = {
        "match": "and",
        "rules": [
            {
                "field": secondary_key,
                "operator": "is not blank",
                "field_name": "SECONDARY_SIGNALS",
            }
        ],
    }
    records = app.get(config["signals_container"], filters=filters)
    signal_field_names = generate_field_name_lookup(records[0])

    # Creating a lookup dict of primary -> secondary signals
    signal_lookup = {}
    for signal_rec in records:
        if signal_rec.data[secondary_key]:
            signal_lookup[signal_rec.data["id"]] = signal_rec.data[
                f"{secondary_key}_raw"
            ]

    # 3. Do for each PM record:
    #   - Set the PM record's COPIED_TO_SECONDARY to True
    #   - For each secondary signal, copy the PM record and attach the appropriate signal
    #   - Update the modified date of the secondary traffic signal, so the data is refreshed on the ODP.
    current_date = date.today().strftime("%Y-%m-%d")

    # Grabbing some useful knack field names
    copied_field_name = find_knack_field_name("COPIED_TO_SECONDARY", pm_field_names)
    signal_field_name = find_knack_field_name("signal", pm_field_names)
    modified_date_field_name = find_knack_field_name(
        "MODIFIED_DATE", signal_field_names
    )

    knack_todos = []
    for pm in pm_records:
        # Set the PM record's COPIED_TO_SECONDARY to True
        data = {"id": pm.data["id"], copied_field_name: True}
        knack_todos.append({"method": "update", "obj": config["object"], "data": data})
        pm.data[copied_field_name] = True

        # For each secondary signal, copy the PM record and attach the appropriate signal
        primary_signal_id = pm.data[f"{signal_field_name}_raw"][0]["id"]
        secondary_signals = signal_lookup[primary_signal_id]
        for secondary in secondary_signals:
            new_rec = {}
            keys = pm.keys()
            keys.remove("id")
            # Copying PM record, we copy the existing value based on the field type.
            for key in keys:
                if pm.fields[key].field_def.type in ["multiple_choice"]:
                    new_rec[key] = pm.data[f"{key}_raw"]
                elif pm.fields[key].field_def.type in ["connection"]:
                    new_rec[key] = [entry["id"] for entry in pm.data[f"{key}_raw"]]
                elif pm.fields[key].field_def.type in [
                    "auto_increment",
                    "concatenation",
                ]:
                    continue
                else:
                    new_rec[key] = pm.data[key]
            # Tagging the signal with the secondary signal's knack record ID
            new_rec[signal_field_name] = secondary["id"]
            knack_todos.append(
                {"method": "create", "obj": config["object"], "data": new_rec}
            )

            # Update the modified date of the secondary traffic signal, so the data is refreshed on the ODP.
            data = {"id": secondary["id"], modified_date_field_name: current_date}
            knack_todos.append(
                {"method": "update", "obj": config["signal_object_id"], "data": data}
            )

    # Sending updates/creates to knack
    logger.info(f"Updating/creating {len(knack_todos)} knack records")
    count = 0
    for knack_job in knack_todos:
        if count % 10 == 0:
            logger.info(f"Uploading record {count} of {len(knack_todos)}")
        res = record_to_knack(
            record=knack_job["data"],
            object_id=knack_job["obj"],
            method=knack_job["method"],
        )
        count += 1


if __name__ == "__main__":
    # CLI arguments definition
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--app-name",
        type=str,
        help="str: Name of the Knack App in knack.py config file",
    )

    parser.add_argument(
        "-c",
        "--container",
        type=str,
        help="str: AKA API view that was created for downloading the location data",
    )

    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
