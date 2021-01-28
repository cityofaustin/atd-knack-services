""" Field maps and handler functions for knack-to-knack translations

Each handler function must accept and return a single value which will be mapped from
the source application(input value) to the destination application(returned value)
"""


def handle_connection(value):
    """
    Return a string of comma-separated values from a connection field type
    """
    if not value:
        return None
    else:
        # expecting a list of dicts like so:
        # [{'id': '5e7b63a0c279e606c645be7d', 'identifier': 'Some String'}]
        identifiers = [conn["identifier"] for conn in value]
        return ", ".join(str(v) for v in identifiers)


FIELD_MAPS = {
    "finance-purchasing": {
        "view_788": [
            # ATD_INVENTORY_ID
            {"src": "field_918", "data-tracker": "field_3812", "primary_key": True,},
            #  STOCK_NUMBER
            {"src": "field_720", "data-tracker": "field_3467",},
            #  CATEGORY
            {"src": "field_363", "data-tracker": "field_243",},
            #  Financial Name
            {"src": "field_364", "data-tracker": "field_244",},
            # Common Name
            {"src": "field_914", "data-tracker": "field_3617",},
            # Unit cost
            {"src": "field_365", "data-tracker": "field_245",},
            # Modified Date
            {"src": "field_374", "data-tracker": "field_1229",},
            # Modified by
            {
                "src": "field_505_raw",
                "data-tracker": "field_1226",
                "handler": handle_connection,
            },
            # Requires FDU Review
            {"src": "field_915", "data-tracker": "field_3803",},
            #  INVENTORY_TRACKING
            {"src": "field_371", "data-tracker": "field_1125",},
            #  STATUS
            {"src": "field_370", "data-tracker": "field_1068",},
            # UNIT_OF_MEASURE
            {"src": "field_377", "data-tracker": "field_2420",},
            # Object code
            {"src": "field_920", "data-tracker": "field_3462",},
        ]
    }
}

