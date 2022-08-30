#!/usr/bin/env python
"""Build street segment geometries from segment IDs in ArcGIS Online.

This script updates records in ArcGIS Online (AGOL) which have been published from
Knack. These records do have geomtries when published from Knack, they merely reference
a COA street segment ID.

This script:
- Downloads any record from AGOL that has been modified since the given date
- Extracts each records street segment IDs, and fetches the segment geometries from the
canonical COA AGOL layer
- Updates each record in AGOL with the complete geometry from all of its segments
"""
import argparse
import os
import re

import arcgis
import arrow

import utils

# docker run --network host -it --rm --env-file env_file -v /Users/john/Dropbox/atd/atd-knack-services:/app atddocker/atd-knack-services:production services/build_segment_geometries.py -l markings_work_orders

SPATIAL_REFERENCE = 4326
URL = "https://austin.maps.arcgis.com"
USERNAME = os.getenv("AGOL_USERNAME")
PASSWORD = os.getenv("AGOL_PASSWORD")
APP_ID = os.getenv("KNACK_APP_ID")
PGREST_JWT = os.getenv("PGREST_JWT")
PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
CHUNK_SIZE = 500
CONFIG = {
    "layers": {
        "markings_jobs": {
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "id": 0,
            "segment_id_field": "STREET_SEGMENT_IDS",
            "modified_date_field": "MODIFIED_DATE",
        },
        "markings_work_orders": {
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "id": 1,
            "segment_id_field": "STREET_SEGMENT_IDS",
            "modified_date_field": "MODIFIED_DATE",
        },
        "markings_contractor_work_orders": {
            "service_id": "7eb2da1d8e6c4f79b368d8e295dec969",
            "id": 0,
            "segment_id_field": "STREET_SEGMENT_IDS",
            "modified_date_field": "MODIFIED_DATE",
        },
    },
}


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def parse_segment_strings(segments_string):
    """Parsing something like this:
    'PAYTON GIN RD (2039939),  COLLINFIELD DR (2010835),  COOPER DR (2010862)'
    Which is indeed subject to change if someone were to modifiy this text formula
    field in Knack."""
    # street segment IDs are 7 digits
    match_pattern = "\d\d\d\d\d\d\d"
    matches = re.findall(match_pattern, segments_string)
    return [int(segment_id) for segment_id in matches]


def get_segment_features(segment_ids, gis):
    # COA transportation_street_segment service
    # https://austin.maps.arcgis.com/home/item.html?id=a78db5b7a72640bcbb181dcb88817652
    service_id = "a78db5b7a72640bcbb181dcb88817652"
    layer_id = 0
    segment_id_field = "SEGMENT_ID"
    service = gis.content.get(service_id)
    layer = service.layers[layer_id]
    where_part = ",".join([str(seg_id) for seg_id in segment_ids])
    # have tested this with 4k+ segnment IDs, and it is performant. segnment IDs being
    # integer types is probably clutch
    where = f"{segment_id_field} in ({where_part})"
    logger.info(f"Getting {len(segment_ids)} street segments...")
    feature_set = layer.query(where=where, out_fields=["SEGMENT_ID"])
    return feature_set.features or []


def build_geometry(segment_ids, segment_features, match_field="SEGMENT_ID"):
    """Finds and merges all segment geometry paths for the given list of segment IDs

    Of interest: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm  # noqa: E501
    """
    paths = []
    for segment_id in segment_ids:
        for feature in segment_features:
            segment_id_current = feature.attributes.get(match_field)
            if segment_id_current == int(segment_id):
                paths += feature.geometry["paths"]
                break
    if not paths:
        return None
    return {"paths": paths, "spatialReference": {"wkid": 102739, "latestWkid": 2277}}


def format_filter_date(date_from_args):
    return (
        "1970-01-01"
        if not date_from_args
        else arrow.get(date_from_args).format("YYYY-MM-DD")
    )


def cli_args():
    args = [
        {
            "name": "--layer-name",
            "flag": "-l",
            "type": str,
            "required": True,
            "help": "The name of layer to process.",
        },
        {
            "name": "--date",
            "flag": "-d",
            "type": str,
            "required": False,
            "help": "An ISO 8601-compliant date string which will be used to query records",
        },
    ]
    parser = argparse.ArgumentParser()
    for arg in args:
        parser.add_argument(f"{arg.pop('name')}", arg.pop("flag"), **arg)
    return parser.parse_args()


def main():
    args = cli_args()
    layer_name = args.layer_name
    logger.info(args)
    service_id = CONFIG["layers"][layer_name]["service_id"]
    layer_id = CONFIG["layers"][layer_name]["id"]
    segment_id_field = CONFIG["layers"][layer_name]["segment_id_field"]
    modified_date_field = CONFIG["layers"][layer_name]["modified_date_field"]
    gis = arcgis.GIS(url=URL, username=USERNAME, password=PASSWORD)
    service = gis.content.get(service_id)
    layer = service.layers[layer_id]
    date_filter = format_filter_date(args.date)

    logger.info(f"Getting {layer_name} features modified since {date_filter}")

    where = f"{modified_date_field} >= '{date_filter}' AND {segment_id_field} IS NOT NULL"  # noqa: E501

    features = layer.query(
        where=where, out_fields=["OBJECTID", modified_date_field, segment_id_field]
    )

    logger.info(f"{len(features)} features to process")

    if not features:
        return

    all_segment_ids = []

    for feature in features:
        # replace stringy segment ids with lists of segment IDs
        segments_string = feature.attributes.get(segment_id_field)
        segments_as_ints = parse_segment_strings(segments_string)
        feature.attributes[segment_id_field] = segments_as_ints
        # collect all segment ids while we're at it
        all_segment_ids += segments_as_ints

    all_segment_ids = list(set(all_segment_ids))

    # fetch all segment features for segment IDs we've collected
    segment_features = get_segment_features(all_segment_ids, gis)

    todos = []

    for feature in features:
        # join segment feature geometries to our features
        segment_ids = feature.attributes.get(segment_id_field)
        feature_geom = build_geometry(segment_ids, segment_features)
        if not feature_geom:
            """
            It is possible that we won't find a matching street segment feature given
            a segment ID. this could happen from a user mis-keying a segment ID
            or because a once-existing segment ID has been removed or modified from
            CTMs street segment layer.
            """
            continue
        object_id = feature.attributes["OBJECTID"]
        todos.append({"attributes": {"OBJECTID": object_id}, "geometry": feature_geom})

    logger.info(f"Updating geometries for {len(todos)} features...")

    for features_chunk in chunks(todos, CHUNK_SIZE):
        logger.info(f"Uploading {len(features_chunk)} records...")
        res = layer.edit_features(updates=features_chunk, rollback_on_failure=False)
        utils.agol.handle_response(res)


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
