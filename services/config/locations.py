LAYER_CONFIG = [
    # layer config for interacting with ArcGIS Online
    # see: http://resources.arcgis.com/en/help/arcgis-rest-api/index.html#//02r3000000p1000000
    {
        "service_name": "BOUNDARIES_single_member_districts",
        "outFields": "COUNCIL_DISTRICT",
        "updateFields": "field_189",  # COUNCIL_DISTRICT
        "layer_id": 0,
        "distance": 33,  # NOTE: This is in meters.
        "units": "esriSRUnit_Foot",  # NOTE: This is not actually in feet. It's in meters.
        #  how to handle query that returns multiple intersection features
        "handle_features": "merge_all",
        "apply_format": False,
    },
    {
        "service_name": "BOUNDARIES_jurisdictions",
        #  will attempt secondary service if no results at primary
        "service_name_secondary": "BOUNDARIES_jurisdictions_planning",
        "outFields": "JURISDICTION_LABEL",
        "updateFields": "field_190",  # JURISDICTION_LABEL
        "layer_id": 0,
        "handle_features": "use_first",
        "apply_format": False,
    },
    {
        "service_name": "TRANSPORTATION_signal_engineer_areas",
        "outFields": "SIGNAL_ENG_AREA",
        "updateFields": "field_188",  # SIGNAL_ENG_AREA
        "layer_id": 0,
        "handle_features": "use_first",
        "apply_format": False,
    },
    {
        "service_name": "EXTERNAL_cmta_stops",
        "outFields": "STOP_ID",
        "updateFields": "field_2040",  # BUS_STOPS
        "layer_id": 0,
        "distance": 107,  # NOTE: This is in meters.
        "units": "esriSRUnit_Foot",  # NOTE: This is not actually in feet. It's in meters.
        "handle_features": "merge_all",
        "apply_format": True,
    },
]