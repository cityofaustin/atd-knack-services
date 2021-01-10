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


def point_geometry(knack_address_field, spatial_reference):
    # see: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm  # noqa E501
    point = {}
    point["spatialReference"] = {"wkid": spatial_reference}
    point["x"] = knack_address_field["longitude"]
    point["y"] = knack_address_field["latitude"]
    return point


def build_feature(
    record, spatial_reference, location_field_id, fields_names_to_sanitize
):
    feature = {}
    feature["attributes"] = sanitize_html(record.format(), fields_names_to_sanitize)
    if location_field_id:
        feature["geometry"] = point_geometry(
            record[location_field_id], spatial_reference
        )
    return feature


def handle_response(response):
    """ arcgis does not raise HTTP errors for data-related issues; we must manually
    parse the response"""
    if not response:
        return
    keys = ["addResults", "updateResults", "deleteResults"]
    # parsing something like this
    # {'addResults': [{'objectId': 3977021, 'uniqueId': 3977021, 'globalId': None, 'success': True}...], ...}
    for key in keys:
        if response.get(key):
            for feature_status in response.get(key):
                if feature_status.get("success"):
                    continue
                else:
                    # when uploading a group of features, if one feature errors, the
                    # rest will error with code 1003: "operation rolled back". we want
                    # to skip these errors until we surface the real culprit in the
                    # group
                    if feature_status["error"]["code"] == 1003:
                        continue
                    raise ValueError(feature_status["error"])
    return
