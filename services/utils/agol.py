from . import shared


def sanitize_html(record, field_names):
    """
    Temporary hack until we disable html content validation on feature services
    """
    for field_name in field_names:
        val = record[field_name]
        if not val:
            continue
        if "<" not in val or ">" not in val:
            continue
        record[field_name] = val.replace("<", "").replace(">", "")
    return record


def point_geometry(knack_address_dict, spatial_reference):
    # see: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm  # noqa E501
    point = {}
    x = knack_address_dict["longitude"]
    y = knack_address_dict["latitude"]
    if not x and not y:
        # knack may hold emptry strings in these positions :(
        return None
    point["spatialReference"] = {"wkid": spatial_reference}
    point["x"] = x
    point["y"] = y
    return point


def multipoint_geometry(knack_address_list, spatial_reference):
    # see: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm  # noqa E501
    points = {"points": []}
    points["spatialReference"] = {"wkid": spatial_reference}
    for knack_address in knack_address_list:
        x = knack_address["longitude"]
        y = knack_address["latitude"]
        if x and y:
            # knack may hold emptry strings in these positions :(
            points["points"].append(
                [knack_address["longitude"], knack_address["latitude"]]
            )
    if not points["points"]:
        return None
    return points


def build_feature(
    record, spatial_reference, location_field_id, fields_names_to_sanitize
):
    feature = {}
    feature["attributes"] = sanitize_html(record.format(), fields_names_to_sanitize)
    # format knack field names as lowercase/no spaces
    feature["attributes"] = shared.format_keys(feature["attributes"])
    # handle geometry
    if location_field_id:
        record_geometry = record[location_field_id]
        if not record_geometry:
            pass
        elif isinstance(record_geometry, dict):
            feature["geometry"] = point_geometry(record_geometry, spatial_reference)
        elif isinstance(record_geometry, list):
            feature["geometry"] = multipoint_geometry(
                record_geometry, spatial_reference
            )
    return feature


def handle_response(response):
    """arcgis does not raise HTTP errors for data-related issues; we must manually
    parse the response"""
    if not response:
        return
    keys = ["addResults", "updateResults", "deleteResults"]
    # parsing something like this
    # {'addResults': [{'objectId': 3977021, 'uniqueId': 3977021, 'globalId': None, 'success': True},...], ...}
    for key in keys:
        if response.get(key):
            for feature_status in response.get(key):
                if feature_status.get("success"):
                    continue
                else:
                    raise ValueError(feature_status["error"])
    return
