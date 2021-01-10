# Yes, knackpy.App handles TZ settings automatically by fetching it from metadata
# but some scripts may use the lower-level knackpy.api functions, which do not access
# app metadata, but *do* need to query Knack by date, and thus need to know the app's
# timezone. You'll probably never need to change this setting.
APP_TIMEZONE = "US/Central"

CONFIG = {
    "data-tracker": {
        "view_197": {
            "description": "Signals data pub view",
            "scene": "scene_73",
            "modified_date_field": "field_205",
            "socrata_resource_id": "p53x-x73x",
            "location_field_id": "field_182",
            "service_id": "e6eb94d1e7cc45c2ac452af6ae6aa534",
            "item_type": "layer",
            "layer_id": 0,
            "upsert_matching_field": "SIGNAL_ID",
        },
        "view_395": {
            "description": "CCTV Cameras",
            "scene": "scene_144",
            "modified_date_field": "field_714",
            "socrata_resource_id": "b4k4-adkb",
            "location_field_id": "field_182",
        },
        "view_2681": {
            "description": "MMC activities",
            "scene": "scene_1075",
            "modified_date_field": "field_2563",
            "socrata_resource_id": "p7pt-re4k",
        },
        "view_2892": {
            "description": "MMC issues",
            "scene": "scene_514",
            "modified_date_field": "field_1385",
            "socrata_resource_id": "v7vh-gbi6",
            "location_field_id": "field_182",
        },
    },
    "signs-markings": {
        "view_3304": {
            "description": "Markings specifications",
            "scene": "scene_1249",
            "modified_date_field": "field_3365",
            "socrata_resource_id": "dp8d-apw9",
        },
        "view_3106": {
            "description": "Signs asset specification actuals",
            "scene": "scene_1249",
            "modified_date_field": "field_3365",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 0,
            "item_type": "layer",
            "location_field_id": "field_3300",
        },
        "view_3107": {
            "description": "Signs work orders",
            "scene": "scene_1249",
            "modified_date_field": "field_3206",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 1,
            "item_type": "layer",
        },
        "view_3126": {
            "description": "Signs and markings work order materials",
            "scene": "scene_1249",
            "modified_date_field": "field_771",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 1,
            "item_type": "table",
        },
        "view_3127": {
            "description": "Signs & markings work order attachments",
            "scene": "scene_1249",
            "modified_date_field": "object_153",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "item_type": "table",
            "layer_id": 0,
        },
    },
    "finance-purchasing": {
        "view_788": {
            "description": "Inventory items",
            "scene": "scene_84",
            "modified_date_field": "field_374",
            "knack_dest_app": "data-tracker",
            "knack_dest_obj": "object_15",
            "knack_matching_field_name": "commodity something",
        },
    },
}
