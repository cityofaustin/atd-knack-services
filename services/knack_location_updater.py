""" Fetch Knack records from Postgres(t) and update the location information """

import argparse
import logging
import os
import requests

import arrow
from config.knack import CONFIG
from config.locations import LAYER_CONFIG
import utils
import knackpy

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")
PGREST_JWT = os.getenv("PGREST_JWT")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
AGOL_USER = os.getenv("AGOL_USERNAME")
AGOL_PASS = os.getenv("AGOL_PASSWORD")


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def get_output_keys():
    """
    Returns the subset of keys that we will send to knack from.
    Is the ID key + any columns that are updated by the location updater
    """
    output_keys = []
    for layer in LAYER_CONFIG:
        output_keys.append(layer["updateFields"])
    output_keys.append("id")
    return output_keys


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


def point_in_poly(service_name, layer_id, params):
    """
    Check if point is within polygon feature and return attributes of containing
    feature. Assume input geometry spatial reference is WGS84.
    docs: http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000p1000000
    """
    query_url = f"https://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/{service_name}/FeatureServer/{layer_id}/query"

    if "spatialRel" not in params:
        params["spatialRel"] = "esriSpatialRelIntersects"

    res = requests.get(query_url, params=params)
    res.raise_for_status()

    return res.json()


def format_stringify_list(input_list):
    """
    Function to format features when merging multiple feature attributes

    Parameters
    ----------
    input_list : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """
    input_list.sort()
    return ", ".join(str(l) for l in input_list)


def get_params(layer_config, point, token):
    """base params for AGOL query request

    Parameters
    ----------
    layer_config : TYPE
        Description

    Returns
    -------
    TYPE
        Description
    """
    params = {
        "f": "json",
        "outFields": "*",
        "where": "1=1",
        "geometry": None,
        "geomtryType": "esriGeometryPoint",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 4326,
        "geometryType": "esriGeometryPoint",
        "distance": None,
        "units": None,
        "token": token,
        "geometry": point
    }

    for param in layer_config:
        if param in params:
            params[param] = layer_config[param]

    return params

def handle_no_features(changed, layer, record):
    """
    Handling the case where we have no features returned from AGOL for record.

    Parameters
    ----------
    changed: bool
        Flag that tells us that we changed something in this record
    layer : dict
        The config information of the layer queried in AGOl.
    record: dict
        The knack record we are potentially editing.

    Returns
    -------
    record: dict
        Edited knack record
    changed: bool
        Flag that tells us that we changed something in this record

    """
    if (
        layer["handle_features"] == "use_first"
        or layer["apply_format"]
    ):
        data = ""
        if record[layer["updateFields"]] != data:
            logger.info(
                f"No features found for ID:{record['id']} was {record[layer['updateFields']]}"
            )
            record[layer["updateFields"]] = data
            changed = True
    elif layer["handle_features"] == "merge_all":
        data = []
        if record[layer["updateFields"]] != data:
            record[layer["updateFields"]] = data
            changed = True

    return record, changed

def handle_features(changed, layer, record, res):
    """
    Handling the case where have features returned from AGOl

    Parameters
    ----------
    changed: bool
        Flag that tells us that we changed something in this record
    layer : dict
        The config information of the layer queried in AGOl.
    record: dict
        The knack record we are potentially editing.
    res: dict
        The response from the AGOL endpoint

    Returns
    -------
    record: dict
        Edited knack record
    changed: bool
        Flag that tells us that we changed something in this record
    """

    # Case for config where we only use one feature
    if layer["handle_features"] == "use_first":
        #  use first feature in results and join feature data to location record
        feature = res["features"][0]
        data = str(feature["attributes"][layer["outFields"]]).strip()

        if record[layer["updateFields"]] != data:
            logger.info(
                f"Change Detected for ID:{record['id']}:{layer['outFields']} from: {record[layer['updateFields']]} to {data}"
            )
            record[layer["updateFields"]] = str(
                feature["attributes"][layer["outFields"]]
            )
            changed = True
    # Case where we use all returned features
    elif layer["handle_features"] == "merge_all":
        #  concatenate feature attributes from each feature and join to record
        features = res["features"]

        data = []
        for feature in features:
            data.append(
                str(feature["attributes"][layer["outFields"]]).strip()
            )

        if layer["apply_format"]:
            data = format_stringify_list(data)
        else:
            record[layer["updateFields"]] = record[
                layer["updateFields"]
            ].split(",")
            record[layer["updateFields"]] = [
                item.strip() for item in record[layer["updateFields"]]
            ]

        if record[layer["updateFields"]] != data:
            logger.info(
                f"Change Detected for ID:{record['id']}:{layer['outFields']} from: {record[layer['updateFields']]} to {data}"
            )
            record[layer["updateFields"]] = data
            changed = True

    return record, changed



def local_timestamp():
    """
    Create a "local" timestamp (in milliseconds), ie local time represented as a unix timestamp.
    Used to set datetimes when writing Knack records, because Knack assumes input
    time values are in local time. Note that when extracing records from Knack,
    timestamps are standard unix timestamps in millesconds (timezone=UTC).
    """
    return arrow.now().replace(tzinfo="UTC").timestamp * 1000


def main(args):
    # Parse Arguments
    app_name = args.app_name
    container = args.container
    filter_iso_date_str = format_filter_date(args.date)
    logger.info(args)

    token = create_login_token()

    # Getting location data from Postgres(t)
    client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    data = client_postgrest.select(
        "knack",
        params={
            "select": "record, updated_at",
            "app_id": f"eq.{APP_ID}",
            "container_id": f"eq.{container}",
            "updated_at": f"gte.{filter_iso_date_str}",
        },
        order_by="record_id",
    )

    object = CONFIG[app_name][container]["object"]
    loc_field = CONFIG[app_name][container]["location_field_id"]
    modified_date_field = CONFIG[app_name][container]["modified_date_field"]
    update_processed_field = CONFIG[app_name][container]["update_processed_field"]
    knack_data = [r["record"] for r in data]
    output_keys = get_output_keys()
    unmatched_locations = []

    for record in knack_data:
        if record[loc_field]:  # ignore records that have a null location record
            point = [
                record[f"{loc_field}_raw"]["longitude"],
                record[f"{loc_field}_raw"]["latitude"],
            ]
            changed = False
            for layer in LAYER_CONFIG:
                params = get_params(layer, point, token)
                try:
                    res = point_in_poly(
                        layer["service_name"], layer["layer_id"], params
                    )
                    if not res["features"] and "service_name_secondary" in layer:
                        # Some layers have a backup secondary layer to check
                        res = point_in_poly(
                            layer["service_name_secondary"], layer["layer_id"], params
                        )
                    if res.get("error"):
                        raise Exception(str(res))
                    if not res["features"]:
                        # Case 1: we have no features found for our record
                        record, changed = handle_no_features(changed, layer, record)
                    else:
                        # Case 2: We did indeed find features for our record
                        record, changed = handle_features(changed, layer, record, res)
                except Exception as e:
                    logger.info(f"Error handling location ID:{record['id']}")
                    logger.info(e)
                    unmatched_locations.append(record)
                    continue
        if changed:
            # Updating a record in Knack
            record = {key: record[key] for key in output_keys}
            # Two additional fields for every record:
            record[update_processed_field] = True
            record[modified_date_field] = local_timestamp()
            try:
                knackpy.api.record(
                    app_id=APP_ID,
                    api_key=API_KEY,
                    obj=object,
                    method="update",
                    data=record,
                )
            except Exception as e:
                logger.info(e.response.text)

    logger.info(unmatched_locations)


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

    parser.add_argument(
        "-d",
        "--date",
        type=str,
        required=False,
        help="An ISO 8601-compliant date string which will be used to query records",
    )

    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
