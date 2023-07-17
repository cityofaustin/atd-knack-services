#!/usr/bin/env python
import argparse
import os
import requests
import time

import arrow
import knackpy

import utils
from config.knack import CONFIG, APP_TIMEZONE

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")
AGOL_USER = os.getenv("AGOL_USERNAME")
AGOL_PASS = os.getenv("AGOL_PASSWORD")

def create_login_token():
    """
    Returns an auth token from AGOL, to hopefully reduce the risk of rate-limiting
    h/t: https://community.esri.com/t5/arcgis-rest-api-questions/using-python-to-generate-access-token-for-an/td-p/1133618
    """
    organizationName = "austin"
    login_url = f"https://{organizationName}.maps.arcgis.com/sharing/generateToken"
    params = {
        "username": AGOL_USER,
        "password": AGOL_PASS,
        "expiration": 60 * 4,  # In minutes
        "f": "json",
        "referer": f"https://{organizationName}.maps.arcgis.com/",
    }
    res = requests.post(url=login_url, data=params)

    return res.json()["token"]

def query_atx_street(segment_id, token):
    url = "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services/TRANSPORTATION_street_segment/FeatureServer/0/query"

    where = "SEGMENT_ID={}".format(segment_id)

    params = {
        "f": "json",
        "where": where,
        "returnGeometry": False,
        "outFields": "*",
        "token": token,
    }

    res = requests.post(url, params=params)
    res.raise_for_status()

    return res.json()

def are_equal(knack_dict, agol_dict):
    # Return True if field values from a knack dict match
    # values in reference ArcGIS Online dict. Only compare keys from the knack dict
    # that are in the reference dict.
    for key in agol_dict:
        # AGOL seems to use empty string, a single space, and None interchangeably.
        if agol_dict[key] == "" or agol_dict[key] == " ":
            agol_dict[key] = None

    mismatched_keys = []
    for key in knack_dict:
        if key in agol_dict:
            if str(knack_dict[key]) != str(agol_dict[key]):
                mismatched_keys.append(key)

    if mismatched_keys:
        logger.info(f"mismatched field(s): {mismatched_keys}")
        return False
    return True

def local_timestamp():
    """
    Create a "local" timestamp (in milliseconds), ie local time represented as a unix timestamp.
    Used to set datetimes when writing Knack records, because Knack assumes input
    time values are in local time.
    """
    return arrow.now("US/Central").replace(tzinfo="UTC").timestamp * 1000

def create_knack_field_mapping(record):
    """
    Returns the field mapping between human-readable names and knack field names
    """
    field_maps = {}
    for key, field in record.fields.items():
        knack_field_id = field.name
        field_maps[knack_field_id] = key

    return field_maps

def rename_record_keys(record, field_maps):
    """
    Renames the keys in a record dictionary with the provided field mapping
    """
    output_record = {}
    for key in record:
        if key in field_maps:
            output_record[field_maps[key]] = record[key]
    return output_record

def update_record(config, record, field_mapping):
    # Return our AGOL/human field names to Knack field names
    record = rename_record_keys(record, field_mapping)
    # Removing white space from str records
    for field in record:
        if type(record[field]) == str:
            record[field] = record[field].strip()
    try:
        knackpy.api.record(
            app_id=APP_ID,
            api_key=API_KEY,
            obj=config["object"],
            method="update",
            data=record,
        )
    except Exception as e:
        raise Exception(e.response.text)

def main(args):
    app_name = args.app_name
    container = args.container
    logger.info(args)
    config = CONFIG[app_name][container]

    # Get token for AGOL
    token = create_login_token()

    # Get knack records on or after the provided modified date/time
    filters = utils.knack.date_filter_on_or_after(
        args.date, config['modified_date_field'], tzinfo=APP_TIMEZONE, use_time=True
    )
    app = knackpy.App(app_id=APP_ID, api_key=API_KEY)
    records = app.get(container, filters=filters)
    records_formatted = [record.format() for record in records]
    if not records_formatted:
        logger.info('No records to update. Doing nothing.')
        return 0
    field_mapping = create_knack_field_mapping(records[0])
    
    unmatched_segments = []
    for street_segment in records_formatted:
        features = query_atx_street(
            street_segment[config["primary_key"]], token
        )
        if features.get("error"):
            # AGOL returns code 200 even for error queries.
            # Let's try the query again
            features = query_atx_street(
                street_segment[config["primary_key"]], token
            )
            if features.get("error"):
                raise Exception(str(features))

        # handling returned segment features from AGOL
        if features.get("features"):
            if len(features["features"]) > 0:
                segment_data = features["features"][0]["attributes"]
                #  we don't want to compare modified dates
                #  because we don't keep that value in sync with the source data on AGOL
                #  because we use our own modified date set in the data tracker
                segment_data.pop(config["modified_date_col_name"])
                street_segment.pop(config["modified_date_col_name"])

                #  compare new data (segment data) against old (street_segment)
                #  we only want to upload values that have changed
                if not are_equal(street_segment, segment_data):
                    logger.info(f'Change detected for segment ID: {street_segment[config["primary_key"]]}')
                    segment_data["id"] = street_segment["id"]
                    segment_data[config["modified_date_col_name"]] = local_timestamp()
                    # Uploading updated data back to Knack
                    update_record(config, segment_data, field_mapping)
            else:
                unmatched_segments.append(street_segment[config["primary_key"]])
                continue
        else:
            unmatched_segments.append(street_segment[config["primary_key"]])
            continue

    if unmatched_segments:
        error_text = "Unmatched street segments: {}".format(
            ", ".join(str(x) for x in unmatched_segments)
        )
        raise Exception(error_text)


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

    parser.add_argument(
        "-d",
        "--date",
        type=str,
        default="1970/01/01",
        help="Date to filter Knack records created/modified after this date. Format: YYYY/MM/DD HH:MM (UTC)",
    )
    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)