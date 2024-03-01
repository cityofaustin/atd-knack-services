#!/usr/bin/env python
import argparse
import os

import knackpy

from config.knack import CONFIG
import utils

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")


def handle_record_types(knack_record):
    """
    Reformat the connection field types and ignore the automatically generated fields
    """
    output_record = {}
    for field_name in knack_record.fields:
        field_data = knack_record.fields[field_name]
        # get list of record IDs for connection fields
        if field_data.field_def.type == "connection":
            if knack_record.get(field_name):
                output_record[field_name] = [
                    item["id"] for item in knack_record.get(field_name)
                ]
            else:
                output_record[field_name] = None
        # ignoring auto-generated fields
        elif field_data.field_def.type in [
            "equation",
            "concatenation",
            "auto_increment",
        ]:
            continue
        # All other record types
        else:
            output_record[field_name] = knack_record.get(field_name)

    return output_record


def assign_requester(data, requester_field_id, copied_by_field_id):
    """
    Makes the requester the person who created the copied record.
    """
    copied_by = data.pop(copied_by_field_id)
    data[requester_field_id] = copied_by
    return data


def main(args):
    # Process arguments
    app_name = args.app_name
    container = args.container
    logger.info(args)
    config = CONFIG[app_name][container]

    # Use a "free" API call to check for if there's purchase requests to be copied
    app = knackpy.App(app_id=APP_ID, api_key=None)
    records = app.get(container, filters=None)

    if len(records) == 0:
        logger.info("No purchase requests to copy, did nothing.")
        return 0

    logger.info(f"Copying {len(records)} Purchase Requests")
    # Creating a copy of the purchase request and assigning it to person requesting the copy
    for purchase_request in records:
        unique_id = purchase_request.get(config["unique_id_field_id"])
        logger.info(f"Copying Purchase Request with ID: {unique_id}")
        data = handle_record_types(purchase_request)
        data = assign_requester(
            data, config["requester_field_id"], config["copied_by_field_id"]
        )

        # set copy PR to "No"
        data[config["copy_field_id"]] = False

        # Create new record that was copied
        copied_record = knackpy.api.record(
            app_id=APP_ID,
            api_key=API_KEY,
            obj=config["object"],
            method="create",
            data=data,
        )
        logger.info(
            f"New Purchase Request record generated with ID: {copied_record.get(config['unique_id_field_id'])}"
        )

        # Update the original copy to remove it from our queue of requested copies
        old_record = {"id": purchase_request.get("id"), config["copy_field_id"]: False}
        original_record = knackpy.api.record(
            app_id=APP_ID,
            api_key=API_KEY,
            obj=config["object"],
            method="update",
            data=old_record,
        )

        # Get the Auto increment field ID, so we can search the PR items table
        item_filter = {
            "match": "and",
            "rules": [
                {
                    "field": config["pr_items"]["pr_field_id"],
                    "operator": "is",
                    "value": unique_id,
                }
            ],
        }
        app = knackpy.App(app_id=APP_ID, api_key=API_KEY)
        item_records = app.get(config["pr_items"]["object"], filters=item_filter)

        logger.info(f"Copying {len(item_records)} Purchase Request items")
        # Copying over PR items to the newly created PR
        for item in item_records:
            item_data = handle_record_types(item)

            # set item connection to copied purchase request record
            item_data[config["pr_items"]["pr_connection_field_id"]] = [
                copied_record["id"]
            ]
            # set item unique ID to purchase request unique ID
            item_data[config["pr_items"]["pr_field_id"]] = copied_record.get(
                config["unique_id_field_id"]
            )
            item_data.pop("id")

            # generates new PR item as a child record to the copied PR
            new_item = knackpy.api.record(
                app_id=APP_ID,
                api_key=API_KEY,
                obj=config["pr_items"]["object"],
                method="create",
                data=item_data,
            )
    return len(records)


if __name__ == "__main__":
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
