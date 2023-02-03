""" Fetch Knack records from Postgres(t) and update the location information """

import os
import requests

from config.knack import CONFIG
import utils
import knackpy


# Future args
container = "view_1201"
app_name = "data-tracker"
object = "object_11"

# Future config
layers_cfg =  [
        # layer config for interacting with ArcGIS Online
        # see: http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000p1000000
        {
            "service_name": "BOUNDARIES_single_member_districts",
            "outFields": "COUNCIL_DISTRICT",
            "updateFields": "field_189", # COUNCIL_DISTRICT
            "layer_id": 0,
            "distance": 33, # NOTE: This is in meters.
            "units": "esriSRUnit_Foot", # NOTE: This is not actually in feet. It's in meters.
            #  how to handle query that returns multiple intersection features
            "handle_features": "merge_all",
            "apply_format": False,
        },
        {
            "service_name": "BOUNDARIES_jurisdictions",
            #  will attempt secondary service if no results at primary
            "service_name_secondary": "BOUNDARIES_jurisdictions_planning",
            "outFields": "JURISDICTION_LABEL",
            "updateFields": "field_190", # JURISDICTION_LABEL
            "layer_id": 0,
            "handle_features": "use_first",
            "apply_format": False,
        },
        {
            "service_name": "TRANSPORTATION_signal_engineer_areas",
            "outFields": "SIGNAL_ENG_AREA",
            "updateFields": "field_188", # SIGNAL_ENG_AREA
            "layer_id": 0,
            "handle_features": "use_first",
            "apply_format": False,
        },
        {
            "service_name": "EXTERNAL_cmta_stops",
            "outFields": "STOP_ID",
            "updateFields": "field_2040", # BUS_STOPS
            "layer_id": 0,
            "distance": 107, # NOTE: This is in meters.
            "units": "esriSRUnit_Foot", # NOTE: This is not actually in feet. It's in meters.
            "handle_features": "merge_all",
            "apply_format": True,
        },
]

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")
PGREST_JWT = os.getenv("PGREST_JWT")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()

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
    return ", ".join(str(l) for l in input_list)

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

def get_params(layer_config):
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
    }

    for param in layer_config:
        if param in params:
            params[param] = layer_config[param]

    return params

filter_iso_date_str = format_filter_date(None)

client_postgrest = utils.postgrest.Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
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

loc_field = CONFIG[app_name][container]["location_field_id"]

knack_data = [r["record"] for r in data]

a = []
for i in knack_data:
    if i['field_732'] == "LOC16-000265" or i['field_732'] == "LOC16-002630":
        a.append(i)
knack_data = a

updated_records = []
unmatched_locations = []
for record in knack_data:
    point = [record[f"{loc_field}_raw"]["longitude"], record[f"{loc_field}_raw"]["latitude"]]

    for layer in layers_cfg:
        layer["geometry"] = point
        params = get_params(layer)

        try:
            res = point_in_poly(layer['service_name'], layer['layer_id'], params)
            if res.get("error"):
                raise Exception(str(res))
            if not res['features']:
                if layer["handle_features"] == "use_first" or layer["apply_format"]:
                    data = ""
                    if record[layer["updateFields"]] != data:
                        print(f"No features found for location ID:{record['field_732']} was {record[layer['updateFields']]}")
                        record[layer["updateFields"]] == data
                        updated_records.append(record)
                if layer["handle_features"] == "merge_all":
                    data = []
                    if record[layer["updateFields"]] != data:
                        record[layer["updateFields"]] == data
                        updated_records.append(record)
                continue
        except Exception as e:
            print(f"Error handling location ID:{record['field_732']}")
            unmatched_locations.append(record)
            continue

        if layer["handle_features"] == "use_first":
            #  use first feature in results and join feature data to location record
            feature = res['features'][0]

            data = str(feature["attributes"][layer["outFields"]]).strip()
            if record[layer["updateFields"]] != data:
                print(f"Change Detected for ID:{record['field_732']}:{layer['outFields']} from: {record[layer['updateFields']]} to {data}")
                record[layer["updateFields"]] = str(feature["attributes"][layer["outFields"]])
                updated_records.append(record)


        elif layer["handle_features"] == "merge_all":
            #  concatenate feature attributes from each feature and join to record
            features = res['features']

            data = []
            for feature in features:
                data.append(str(feature["attributes"][layer["outFields"]]).strip())

            if layer["apply_format"]:
                data = format_stringify_list(data)
            else:
                record[layer["updateFields"]] = record[layer["updateFields"]].split(",")
                record[layer["updateFields"]] = [item.strip() for item in record[layer["updateFields"]]]

            if record[layer["updateFields"]] != data:
                print(f"Change Detected for ID:{record['field_732']}:{layer['outFields']} from: {record[layer['updateFields']]} to {data}")
                record[layer["updateFields"]] = data
                updated_records.append(record)

count = 0

output_keys = []
for layer in layers_cfg:
    output_keys.append(layer['updateFields'])
output_keys.append("id")

for rec in updated_records:
    rec = {key: rec[key] for key in output_keys}
    rec["UPDATE_PROCESSED"] = True
    if count % 10 == 0:
        print(f"Uploading record {count} of {len(updated_records)}")
    try:
        knackpy.api.record(
        app_id=APP_ID,
        api_key=API_KEY,
        obj=object,
        method="update",
        data=record,
        )
    except Exception as e:
        print(e.response.text)
    count += 1
