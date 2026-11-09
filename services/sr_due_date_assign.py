import argparse
import logging
import os
import sys

import arrow
import knackpy
from config.sr_due_date import CONFIG


APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")


def sr_filter(sr_id, flex_note_code_field_id, sr_field_id):
    """
    Define knack filter to filter flex note records
    matching flex note code SRSLADAT and service request id
    """
    return {
        "match": "and",
        "rules": [
            {
                "field": f"{flex_note_code_field_id}",
                "operator": "is",
                "value": f"SRSLADAT",
            },
            {"field": f"{sr_field_id}", "operator": "is", "value": f"{sr_id}"},
        ],
    }


def format_due_date(date):
    """
    Parse date and return as mm/dd/yyyy.

    Input format, e.g.: 'DEC 04, 2018'
    """
    date_str = arrow.get(date, "MMM DD, YYYY").format("MM/DD/YYYY")
    return date_str


def main(args):
    app_name = args.app_name
    logging.info(app_name)

    if app_name not in ["data_tracker", "signs_markings"]:
        raise ValueError(f"{app_name} not data_tracker or signs_markings")

    for config_name in CONFIG.keys():
        if config_name == app_name:
            app_config = CONFIG[config_name]

    logging.info(f"Requesting service requests for {app_name}")
    records = knackpy.api.get(
        app_id=APP_ID,
        api_key=API_KEY,
        scene=app_config["issues"]["scene"],
        view=app_config["issues"]["view"],
    )

    for sr in records:
        filters = sr_filter(
            sr[app_config["issues"]["sr_field_id"]],
            app_config["flex_notes"]["flex_question_code_field_id"],
            app_config["flex_notes"]["sr_id_field"],
        )

        logging.info(
            f"Looking up flex note for {sr[app_config["issues"]["sr_field_id"]]}"
        )

        flex_note = knackpy.api.get(
            view=app_config["flex_notes"]["view"],
            scene=app_config["flex_notes"]["scene"],
            app_id=APP_ID,
            api_key=API_KEY,
            filters=filters,
        )

        if not flex_note:
            continue


        """
        Always take the first due date in the list. there are occasionally duplicate
        due date flex records for one SR. We don't know why.
        """
        due_date = format_due_date(
            flex_note[0].get(app_config["flex_notes"]["flex_attribute_value_id"])
        )

        print(due_date)

        break




        # record = {cfg["issues"]["due_date_field_id"]: due_date, "id": sr["id"]}

        # res = knackpy.record(
        #     record,
        #     obj_key=cfg["issues"]["ref_obj"][0],
        #     app_id=KNACK_CREDENTIALS[app_name]["app_id"],
        #     api_key=KNACK_CREDENTIALS[app_name]["api_key"],
        #     method="update",
        # )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--app-name",
        type=str,
        help="str: Name of the Knack App, data_tracker or signs_markings",
    )

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    args = parser.parse_args()
    main(args)
