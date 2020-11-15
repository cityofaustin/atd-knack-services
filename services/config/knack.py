# Yes, knackpy.App handles TZ settings automatically by fetching it from metadata
# but some scripts may use the lower-level knackpy.api functions, which do not access
# app metadata, but *do* need to query Knack by date, and thus need to know the app's
# timezone. You'll probably never need to change this setting.
APP_TIMEZONE = "US/Central"

CONFIG = {
    "data-tracker": {
        "object_11": {
            "description": "Locations object",
            "modified_date_field": "field_508",
        },
        "view_197": {
            "description": "Signals data pub view",
            "scene": "scene_73",
            "modified_date_field": "field_205",
            "socrata_resource_id": "p53x-x73x",
            "location_fields": ["field_182"],
            "service_id": "e6eb94d1e7cc45c2ac452af6ae6aa534",
            "layer_id": 0,
            "upsert_matching_field": "SIGNAL_ID"
        },
        "view_395": {
            "description": "CCTV Cameras",
            "scene": "scene_144",
            "modified_date_field": "field_714",
            "socrata_resource_id": "b4k4-adkb",
            "location_fields": ["field_182"],
        },
        "view_2681": {
            "description": "MMC activities",
            "scene": "scene_1075",
            "modified_date_field": "field_2563",
            "socrata_resource_id": "p7pt-re4k",
        },
    }
}
