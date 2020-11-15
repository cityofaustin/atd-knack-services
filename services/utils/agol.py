def point_geometry(knack_address_field, spatial_reference):
    # see: https://developers.arcgis.com/documentation/common-data-types/geometry-objects.htm
    point = {}
    point["spatialReference"] = {"wkid": spatial_reference}
    point["x"] = knack_address_field["longitude"]
    point["y"] = knack_address_field["latitude"]
    return point


def build_feature(record, spatial_reference, location_field_id):
    feature = {}
    feature["attributes"] = record.format()
    feature["geometry"] = point_geometry(record[location_field_id], spatial_reference)
    return feature