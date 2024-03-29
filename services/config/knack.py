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
            "object": "object_12",
            "dest_apps": {
                "smart-mobility": {
                    "container": "view_396",
                    "description": "Artbox Locations",
                    "modified_date_field": "field_391",
                    "object": "object_26",
                },
            },
        },
        "view_395": {
            "description": "CCTV Cameras",
            "scene": "scene_144",
            "modified_date_field": "field_714",
            "socrata_resource_id": "b4k4-adkb",
            "location_field_id": "field_182",
            "service_id": "52f2b5e51b9a4b5e918b0be5646f27b2",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_2681": {
            "description": "MMC activities",
            "scene": "scene_1075",
            "modified_date_field": "field_2563",
            "socrata_resource_id": "p7pt-re4k",
        },
        "view_2362": {
            "description": "MMC Issue Auto Assign Queue",
            "scene": "scene_514",
            "modified_date_field": "field_1385",
            "object": "object_83",  # Needed for sr_asset_assign
            "assign_status_field_id": "field_2813",  # Needed for sr_asset_assign
            "asset_type_field_id": "field_1649",  # Needed for sr_asset_assign
            "connection_field_keys": {
                "signals": "field_1367"
            },  # Needed for sr_asset_assign
            "x_field": "field_1402",  # CSR_X_VALUE
            "y_field": "field_1401",  # CSR_Y_VALUE
        },
        "view_2892": {
            "description": "MMC issues",
            "scene": "scene_514",
            "modified_date_field": "field_1385",
            "socrata_resource_id": "v7vh-gbi6",
            "location_field_id": "field_182",
        },
        "view_2863": {
            "description": "Inventory items (finance system integration + socrata pub)",
            "scene": "scene_1170",
            "modified_date_field": "field_1229",
            "socrata_resource_id": "hcaw-evi2",
            "append_timestamps_socrata": {"key": "published_date"},
            "no_replace_socrata": True,
        },
        "view_2908": {
            "description": "Metrobike kiosks",
            "scene": "scene_514",
            "modified_date_field": "field_3798",
            "service_id": "7d4d0b1369504383a42b943bd9c03f9a",
            "layer_id": 0,
            "item_type": "layer",
            "location_field_id": "field_3818",
            "socrata_resource_id": "qd73-bsdg",
        },
        "view_1564": {
            "description": "Digital Messaging Signs",
            "scene": "scene_569",
            "modified_date_field": "field_1658",
            "service_id": "e7104494593d4a44a2529e4044ef7d5d",
            "socrata_resource_id": "4r2j-b4rx",
            "location_field_id": "field_182",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_1829": {
            "description": "Work Orders Signals",
            "scene": "scene_683",
            "modified_date_field": "field_1074",
            "socrata_resource_id": "hst3-hxcz",
            "location_field_id": "field_182",
        },
        "view_1563": {
            "description": "Flashing Beacons",
            "scene": "scene_568",
            "modified_date_field": "field_1701",
            "socrata_resource_id": "wczq-5cer",
            "location_field_id": "field_182",
            "service_id": "6c4392540b684d598c72e52206d774be",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_1333": {
            "description": "Detectors",
            "scene": "scene_468",
            "modified_date_field": "field_1533",
            "socrata_resource_id": "qpuw-8eeb",
            "location_field_id": "field_182",
            "service_id": "47d17ff3ce664849a16b9974979cd12e",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_540": {
            "description": "Travel Sensors",
            "scene": "scene_188",
            "modified_date_field": "field_710",
            "socrata_resource_id": "6yd9-yz29",
            "location_field_id": "field_182",
            "service_id": "9776d3e894a74521a7f63443f7becc7c",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_1063": {
            "description": "Signal Retiming",
            "scene": "scene_375",
            "modified_date_field": "field_1257",
            "socrata_resource_id": "g8w2-8uap",
        },
        "view_1597": {
            "description": "Pole Attachments",
            "scene": "scene_589",
            "modified_date_field": "field_1813",
            "socrata_resource_id": "btg5-ebcy",
            "location_field_id": "field_182",
            "service_id": "3a5a777f780447db940534b5808d4ba7",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_1201": {
            "description": "Arterial Management Locations",
            "scene": "scene_425",
            "modified_date_field": "field_508",
            "location_field_id": "field_182",
            "service_id": "66f4b5b0339d4275b64f265dd59727e5",
            "update_processed_field": "field_1357",  # Needed for location_updater
            "object": "object_11",  # Needed for location_updater
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_1567": {
            "description": "Signal Cabinets",
            "scene": "scene_571",
            "modified_date_field": "field_1793",
            "socrata_resource_id": "x23u-shve",
            "location_field_id": "field_1878",
            "service_id": "c3fd3bb177cc4291880bbe8c630ed5c4",
            "layer_id": 0,
            "item_type": "layer",
        },
        "view_3003": {
            "description": "Signal detection status logs",
            "scene": "scene_514",
            "modified_date_field": "field_2565",
            "socrata_resource_id": "e4b6-xseb",
        },
        "view_3086": {
            "description": "School Beacons",
            "scene": "scene_418",
            "modified_date_field": "field_4038",
            "location_field_id": "field_182",
            "service_id": "ebde70df086942c286dcf9f3f3449f2f",
            "layer_id": 0,
            "item_type": "layer",
            "socrata_resource_id": "8whb-sg4d",
        },
        "view_4027": {
            "description": "School zone beacon zones",
            "scene": "scene_1609",
            "modified_date_field": "field_1304",
            "socrata_resource_id": "vz34-kwdc",
        },
        "view_3488": {
            "description": "Signal studies for signal evaluations map",
            "scene": "scene_1233",
            "modified_date_field": "field_3671",
            "location_field_id": "field_182",
            "socrata_resource_id": "h4cy-hpgs",
        },
        "view_3814": {
            "description": "Corridor retiming",
            "scene": "scene_1526",
            "modified_date_field": "field_4169",
            "socrata_resource_id": "bp5z-kciq",
        },
        "view_1198": {
            "description": "Street segments",
            "scene": "scene_424",
            "modified_date_field": "field_144",
            "modified_date_col_name": "MODIFIED_DATE",
            "primary_key": "SEGMENT_ID_NUMBER",
            "object": "object_7",
        },
        "view_3897": {
            "description": "AMD Inventory transactions",
            "scene": "scene_1555",
            "modified_date_field": "field_771",
            "socrata_resource_id": "3tjk-hanz",
        },
        "view_200": {
            "description": "AMD signal & PHB requests",
            "scene": "scene_75",
            "location_field_id": "field_182",
            "service_id": "c8577cef82ef4e6a89933a7a216f1ae1",
            "item_type": "layer",
            "layer_id": 0,
            "modified_date_field": "field_217",
            # socrata publishing is currently disabled because the data has extra ranking columns
            # that were populated by a legacy script. we are waiting on direction from AMD
            # before we switch this on
            # "socrata_resource_id": "f6qu-b7zb"
        },
    },
    "signs-markings": {
        "view_3099": {
            "description": "Markings work orders",
            "scene": "scene_1249",
            "modified_date_field": "field_2150",
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "layer_id": 1,
            "item_type": "layer",
            "location_field_id": None,
            "socrata_resource_id": "nyhn-669r",
        },
        "view_3628": {
            "description": "Contract work orders",
            "scene": "scene_1249",
            "modified_date_field": "field_3774",
            "service_id": "7eb2da1d8e6c4f79b368d8e295dec969",
            "layer_id": 0,
            "item_type": "layer",
            "location_field_id": None,
            "socrata_resource_id": "5dex-63ir",
        },
        "view_3100": {
            "description": "Markings jobs",
            "scene": "scene_1249",
            "modified_date_field": "field_2196",
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "layer_id": 0,
            "item_type": "layer",
            "location_field_id": None,
            "socrata_resource_id": "vey3-7n3x",
        },
        "view_3096": {
            "description": "Markings work order attachments",
            "scene": "scene_1249",
            "modified_date_field": "field_2407",
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "layer_id": 0,
            "item_type": "table",
            "location_field_id": None,
        },
        "view_3103": {
            "description": "Markings asset specification actuals",
            "scene": "scene_1249",
            "modified_date_field": "field_3365",
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "layer_id": 1,
            "item_type": "table",
            "location_field_id": None,
        },
        "view_3104": {
            "description": "Markings job materials",
            "scene": "scene_1249",
            "modified_date_field": "field_771",
            "service_id": "a9f5be763a67442a98f684935d15729b",
            "layer_id": 2,
            "item_type": "table",
            "location_field_id": None,
        },
        "view_3106": {
            "description": "Signs asset specification actuals",
            "scene": "scene_1249",
            "modified_date_field": "field_3365",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 0,
            "item_type": "layer",
            "location_field_id": "field_3300",
            "socrata_resource_id": "jji9-2k5d",
        },
        "view_3107": {
            "description": "Signs work orders",
            "scene": "scene_1249",
            "modified_date_field": "field_3206",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 1,
            "item_type": "layer",
            "location_field_id": "field_3300",
            "socrata_resource_id": "ivss-na93",
        },
        "view_3126": {
            "description": "Signs work order materials",
            "scene": "scene_1249",
            "modified_date_field": "field_771",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "layer_id": 1,
            "item_type": "table",
        },
        "view_3127": {
            "description": "Signs work order attachments",
            "scene": "scene_1249",
            "modified_date_field": "field_2568",
            "service_id": "93e29b23c39b4110ab0bbefde79b4063",
            "item_type": "table",
            "layer_id": 0,
        },
        # Note that views 3307 and 3528 push to the same socrata dataset. This object is a child to
        # both work_orders_markings and work_orders_signs - which share duplicate field names, notably
        # ATD_WORK_ORDER_ID, WORK_TYPE, and LOCATION_NAME. So we source the time logs from two
        # similar views, one with connection fields added from markings and the other with fields
        # added from signs. They map one set of columns in Socrata, which matches on the knack field
        # name rather than key.
        "view_3307": {
            "description": "Work Order Markings Time Logs",
            "scene": "scene_1249",
            "modified_date_field": "field_2559",
            "socrata_resource_id": "qvth-gwdv",
        },
        "view_3528": {
            "description": "Work Order Signs Time Logs",
            "scene": "scene_1249",
            "modified_date_field": "field_2559",
            "socrata_resource_id": "qvth-gwdv",
        },
        # Similarly views 3526 and 3527 push to the same socrata dataset (see note above)
        "view_3526": {
            "description": "Signs reimburesement tracking",
            "scene": "scene_1249",
            "modified_date_field": "field_4000",
            "socrata_resource_id": "pma8-yy5k",
        },
        "view_3527": {
            "description": "Markings reimburesement tracking",
            "scene": "scene_1249",
            "modified_date_field": "field_4000",
            "socrata_resource_id": "pma8-yy5k",
        },
    },
    "finance-purchasing": {
        "view_211": {
            "description": "Purchase Requests",
            "scene": "scene_84",
            "object": "object_1",
            "requester_field_id": "field_12",
            "copied_by_field_id": "field_283",
            "copy_field_id": "field_268",
            "unique_id_field_id": "field_11",
            "pr_items": {
                "object": "object_4",
                "pr_field_id": "field_269",
                "pr_connection_field_id": "field_20",
            },
        },
        "view_788": {
            "description": "Inventory items",
            "scene": "scene_84",
            "modified_date_field": "field_374",
            "dest_apps": {
                "data-tracker": {
                    "container": "view_2863",
                    "description": "Inventory items",
                    "modified_date_field": "field_1229",
                    "object": "object_15",
                },
            },
        },
    },
    "smart-mobility": {
        "view_396": {
            "description": "Artbox Signal Locations",
            "scene": "scene_146",
            "modified_date_field": "field_391",
        }
    },
    "row": {
        "view_483": {
            "description": "TCP Submissions",
            "scene": "scene_221",
            "modified_date_field": "field_550",
            "socrata_resource_id": "vz5j-8n8f",
        }
    },
    "hr-manager": {
        "view_684": {
            "description": "TPW Employees",
            "scene": "scene_321",
            "modified_date_field": "field_265",
            "dest_apps": {
                "tpw-hire": {
                    "container": "view_148",
                    "description": "TPW Employees",
                    "modified_date_field": "field_179",
                    "object": "object_16",
                },
            },
        }
    },
    "tpw-hire": {
        "view_148": {
            "description": "TPW Employees",
            "scene": "scene_69",
            "modified_date_field": "field_179",
        }
    },
}
