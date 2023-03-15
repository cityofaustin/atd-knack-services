""" Fetch 3-1-1 SR records from Knack and assign a nearby asset """

import argparse
import logging
import os
import requests

import arrow
from config.knack import CONFIG, APP_TIMEZONE
from config.locations import ASSET_CONFIG
import utils
import knackpy

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")
PGREST_JWT = os.getenv("PGREST_JWT")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
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
        "geomtryType": "esriGeometryPoint",
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


def handle_features(layer, record, connected_field, res):
    """
    Handling the case where have features returned from AGOl

    Parameters
    ----------
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

    asset_id = res["features"][0]["attributes"].get(layer["layer"]["primary_key"])

    # Searching knack for the matching signal record
    kwargs = {"scene": layer["scene"], "view": layer["view"]}
    filters = asset_filter(layer["primary_key"], asset_id)
    asset = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, filters=filters, **kwargs)

    # both of these cases should never happen if AGOL is in sync with Knack
    if len(asset) > 1:
        raise Exception("More than one Knack asset found for given asset id.")
    elif len(asset) == 0:
        raise Exception("No corresponding Knack asset found for GIS feature.")

    asset_id = asset[0]["id"]
    record[connected_field] = asset_id
    return record


def local_timestamp():
    """
    Create a "local" timestamp (in milliseconds), ie local time represented as a unix timestamp.
    Used to set datetimes when writing Knack records, because Knack assumes input
    time values are in local time.
    """
    return arrow.now("US/Central").replace(tzinfo="UTC").timestamp() * 1000


def main(args):
    # Parse Arguments
    app_name = args.app_name
    container = args.container
    logger.info(args)

    # Get AGOL Token
    token = create_login_token()

    # Getting SR data from Knack
    config = CONFIG[app_name][container]
    modified_date_field = config["modified_date_field"]
    kwargs = {"scene": config["scene"], "view": args.container}
    data = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, **kwargs)

    if len(data) == 0:
        logger.info("No SRs waiting in queue to be processed, doing nothing.")
        return 0


    object_id = config["object"]
    status_field = config["assign_status_field_id"]
    connected_field = config["connection_field_keys"][args.asset]
    output_keys = ["id", config["asset_type_field_id"], connected_field]
    layer = ASSET_CONFIG[args.asset]

    for record in data:
        if (
            record[config["x_field"]] and record[config["y_field"]]
        ):  # ignore records that have a null location data
            point = [
                record[config["x_field"]],
                record[config["y_field"]],
            ]
            params = get_params(layer["layer"], point, token)
            res = point_in_poly(
                layer["layer"]["service_name"], layer["layer"]["layer_id"], params
            )
            # we have to manually check for response errors. The API returns `200` regardless
            if res.get("error"):
                raise Exception(str(res))
            if not res["features"]:
                # Only need to send the status no_asset_found
                record[status_field] = "no_asset_found"
                record[config["asset_type_field_id"]] = ""
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
                record = handle_features(layer, record, connected_field, res)
                record[config["asset_type_field_id"]] = layer["display_name"]

            # Updating a record in Knack
            record = {key: record[key] for key in output_keys}
            # Add modified date field for every record:
            record[modified_date_field] = local_timestamp()
            try:
                knackpy.api.record(
                    app_id=APP_ID,
                    api_key=API_KEY,
                    obj=object_id,
                    method="update",
                    data=record,
                )
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
        help="str: Name of the asset to search for potential matches",
    )
    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
