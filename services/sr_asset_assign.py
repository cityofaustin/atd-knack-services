""" Fetch 3-1-1 SR records from Knack and assign a nearby asset """

import argparse
import logging
import os
import requests

import arrow
from config.knack import CONFIG
from config.locations import ASSET_CONFIG
import utils
import knackpy

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")
AGOL_USER = os.getenv("AGOL_USERNAME")
AGOL_PASS = os.getenv("AGOL_PASSWORD")
KNACK_API_USER_EMAIL = os.getenv("AGOL_PASSWORD")
KNACK_API_USER_PW = os.getenv("AGOL_PASSWORD")


def create_agol_login_token():
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


def create_knack_login_token():
    """Get a knack user auth token so that we can submit data through an
    authenticated form in the Data Tracker.
    See: https://docs.knack.com/docs/user-tokens

    Returns:
        Str: the token string
    """
    data = {"email": KNACK_API_USER_EMAIL, "password": KNACK_API_USER_PW}
    url = f"https://api.knack.com/v1/applications/{APP_ID}/session"
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, headers=headers, json=data)
    res.raise_for_status()
    return res.json()["session"]["user"]["token"]


def point_in_poly(service_name, layer_id, params):
    """
    Check if point is within polygon feature and return attributes of containing
    feature. Assume input geometry spatial reference is 2277 (NAD83 / Texas Central (ftUS)).
    docs: http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000p1000000
    """
    query_url = f"https://services.arcgis.com/0L95CJ0VTaxqcmED/ArcGIS/rest/services/{service_name}/FeatureServer/{layer_id}/query"
    if "spatialRel" not in params:
        params["spatialRel"] = "esriSpatialRelIntersects"
    res = requests.get(query_url, params=params)
    res.raise_for_status()
    return res.json()


def asset_filter(field, value):
    """
    Provides a filter argument for a searching for matching knack records

    Parameters
    ----------
    field : string
        Field we are querying, must start with field_
        ex: "field_123"
    value : string
        Key value we are searching for.

    Returns
    -------
    dict
        formatted filter argument for Knackpy

    """
    return {
        "match": "or",
        "rules": [{"field": f"{field}", "operator": "is", "value": f"{value}"}],
    }


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
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
        "inSR": 2277,
        "geometryType": "esriGeometryPoint",
        "distance": None,
        "units": None,
        "token": token,
        "geometry": point,
    }

    for param in layer_config:
        if param in params:
            params[param] = layer_config[param]

    return params


def local_timestamp():
    """
    Create a "local" timestamp (in milliseconds), ie local time represented as a unix timestamp.
    Used to set datetimes when writing Knack records, because Knack assumes input
    time values are in local time.
    """
    return arrow.now("US/Central").replace(tzinfo="UTC").timestamp * 1000


def submit_knack_form(token, record):
    """
    Submit data via Knack form view.
    Docs: https://docs.knack.com/docs/view-based-requests
    """
    url = f"https://api.knack.com/v1/pages/scene_428/views/view_2367/records/{record['id']}"
    headers = {"X-Knack-Application-Id": APP_ID, "Authorization": token}
    res = requests.put(url, headers=headers, json=record)
    res.raise_for_status()
    return res


def main(args):
    # Parse Arguments
    app_name = args.app_name
    container = args.container
    logger.info(args)

    # Get AGOL Token
    token_agol = create_agol_login_token()

    # Getting SR data from Knack
    config = CONFIG[app_name][container]
    modified_date_field = config["modified_date_field"]
    kwargs = {"scene": config["scene"], "view": args.container}
    data = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, **kwargs)

    if len(data) == 0:
        logger.info("No SRs waiting in queue to be processed, doing nothing.")
        return 0

    status_field = config["assign_status_field_id"]
    connected_field = config["connection_field_keys"][args.asset]
    output_keys = ["id", config["asset_type_field_id"], connected_field]
    layer = ASSET_CONFIG[args.asset]

    token_knack = None

    for record in data:
        if (
            record[config["x_field"]] and record[config["y_field"]]
        ):  # ignore records that have a null location data
            point = [
                record[config["x_field"]],
                record[config["y_field"]],
            ]
            params = get_params(layer["layer"], point, token_agol)
            res = point_in_poly(
                layer["layer"]["service_name"], layer["layer"]["layer_id"], params
            )
            # we have to manually check for response errors. The API returns `200` regardless
            if res.get("error"):
                raise Exception(str(res))
            if not res["features"]:
                # Only need to send the status no_asset_found
                record[status_field] = "no_asset_found"
                record[
                    config["asset_type_field_id"]
                ] = "No Asset / Unkown Location / Other"
                record[connected_field] = ""
                logger.info(f"No Assets found for ID: {record['id']}.")
            elif len(res["features"]) != 1:
                # Ignore records with multiple assets found
                logger.info(
                    f"Multiple Assets found for ID: {record['id']}, skipping updating this record."
                )
                continue
            if len(res["features"]) == 1:
                logger.info(f"One Asset found for ID: {record['id']}.")
                # assumes AGOL layer has 'id' column which holds each record's Knack ID
                record[connected_field] = res["features"][0]["attributes"]["id"]
                record[config["asset_type_field_id"]] = layer["display_name"]

            # Get knack token if we haven't fetched one yet
            if not token_knack:
                token_knack = create_knack_login_token()

            # Updating a record in Knack
            record = {key: record[key] for key in output_keys}
            # Add modified date field for every record:
            record[modified_date_field] = local_timestamp()
            try:
                submit_knack_form(token_knack, record)
            except Exception as e:
                logger.info(e.response.text)


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
        "-s",
        "--asset",
        type=str,
        choices=["signals"],
        help="str: Name of the asset to search for potential matches",
    )
    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
