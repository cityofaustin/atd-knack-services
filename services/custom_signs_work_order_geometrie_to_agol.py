#!/usr/bin/env python
"""Deprecated / Not in use. Commiting here for future reference of some useful
approaches to arcgis interactions. will revist when working on markings data pub


Creates multi-point street sign work order geometries from their child asset
specification actuals locations.

Street sign work orders have a one-to-many relatinship with asset specification actuals.
The asset spec actuals hold an individual point geometry, while the street sign work
orders hold a multipoint geometry which is a composite its asset spec actuals.

It works like this:
The signs work order data is comprised of five knack objects:
- work order
    |- (many) work order locations
        |- (many) asset specification actuals
    |- (many) attachments
    |- (many) materials 

These objects are translated to four AGOL items which are linked through a relationship
class:
- work orders (layer, multipoint geometry)
    |- asset specification actuals (layer, point geometry)
    |- attachments (table)
    |- materials (table)

As you can see, the "work order locations" object is not represented in AGOL. Instead,
we attach each location point geometry to it's child asset specifications. Flattening
this relationship simplies reporting and analysis by removing the intermediary locations
table that sits between work orders and their asset specification actuals.

The data for each of these four items flows through the normal
services/records_to_agol.py. However, work orders  

Document why—we drive this from asset specs (they are created after location) and
why we just fetch all work orders from the date rather than by ID ("its much faster")
"""
import os

import arcgis
import arrow

import utils

URL = "https://austin.maps.arcgis.com"
USERNAME = os.getenv("AGOL_USERNAME")
PASSWORD = os.getenv("AGOL_PASSWORD")
SERVICE_ID = "93e29b23c39b4110ab0bbefde79b4063"
WORK_ORDERS_LAYER_ID = 1
ASSET_SPEC_LAYER_ID = 0


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def format_filter_date(date_from_args):
    return "1970-01-01" if not date_from_args else arrow.get(date_from_args).isoformat()


def chunked_date_query(
    layer, date_str, date_field, out_fields=["OBJECTID", "ATD_WORK_ORDER_ID"], chunk_size=500, return_geometry=True
):
    offset = 0
    all_features = []
    while True:
        feature_set = layer.query(
            where=f"{date_field} >= '{date_str}'",
            out_fields=out_fields,
            result_record_count=chunk_size,
            result_offset=offset,
            return_all_records=False,
            return_geometry=return_geometry
        )
        if not feature_set:
            break
        all_features += [f for f in feature_set]
        offset += chunk_size
    return all_features


def chunked_feature_attribute_query(layer, field_name, match_values):
    all_features = []
    for chunk in chunks(match_values, 1000):
        print("chunk")
        quoted_values = ",".join([f"'{val} '" for val in match_values])
        where = f"{field_name} in ({quoted_values})"
        feature_set = layer.query(
            where=where, return_geometry=False, out_fields=[field_name, "OBJECTID"]
        )
        all_features += [f for f in feature_set]
    return all_features


def build_indexed_geometries(features, key="ATD_WORK_ORDER_ID"):
    # see: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm
    index = {}
    for f in features:
        f_id = f.attributes.get(key)
        index.setdefault(f_id, {"points": []})
        index[f_id]["points"].append([f.geometry["x"], f.geometry["y"]])
    return index


def main():
    args = utils.args.cli_args(["date"])
    filter_iso_date_str = format_filter_date(args.date)
    gis = arcgis.GIS(url=URL, username=USERNAME, password=PASSWORD)
    service = gis.content.get(SERVICE_ID)
    layer_asset_spec = service.layers[ASSET_SPEC_LAYER_ID]
    layer_work_orders = service.layers[WORK_ORDERS_LAYER_ID]

    asset_spec_feature_set = chunked_date_query(
        layer_asset_spec, filter_iso_date_str, "MODIFIED_DATE"
    )

    logger.info(f"{len(asset_spec_feature_set)} asset specs fetched")

    work_order_feature_set = chunked_date_query(
        layer_work_orders, filter_iso_date_str, "CREATED_DATE", return_geometry=False
    )

    updated_features = []

    logger.info("building geoms")

    geometry_index = build_indexed_geometries(asset_spec_feature_set)

    for f in work_order_feature_set:
        geom = geometry_index.get(f.attributes["ATD_WORK_ORDER_ID"])
        if geom:
            f.geometry = geom
            updated_features.append(f)

    logger.info(f"sending updates on {len(updated_features)} wos")

    for chunk in chunks(updated_features, 200):
        res = layer_work_orders.edit_features(updates=chunk)
        utils.agol.handle_response(res)


if __name__ == "__main__":
    logger = utils.logging.getLogger(__file__)
    main()
