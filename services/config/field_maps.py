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


def handle_strip(value):
    try:
        return value.strip()
    except AttributeError:
        return value


FIELD_MAPS = {
    "data-tracker": {
        "view_197": [
            # Signal ID
            {
                "src": "field_199_raw",
                "smart-mobility": "field_380",
                "primary_key": True,
            },
            # Location Name
            {
                "src": "field_211_raw",
                "smart-mobility": "field_382",
                "handler": handle_strip,
            },
            # Signal Status
            {
                "src": "field_491",
                "smart-mobility": "field_383",
            },
            # Modified Date/time
            {
                "src": "field_205",
                "smart-mobility": "field_391",
            },
            # Location ID
            {
                "src": "field_209",
                "smart-mobility": "field_381",
            },
            # WEB_URL_GENERATOR_PM
            {
                "src": "field_3399",
                "smart-mobility": "field_384",
            },
            # Council district
            {
                "src": "field_1256",
                "smart-mobility": "field_385",
            },
            # Signal Name
            {
                "src": "field_1058",
                "smart-mobility": "field_386",
            },
            # Signal Engineer Area
            {
                "src": "field_1857",
                "smart-mobility": "field_387",
            },
        ],
    },
    "finance-purchasing": {
        "view_788": [
            # ATD_INVENTORY_ID
            {
                "src": "field_918",
                "data-tracker": "field_3812",
                "primary_key": True,
            },
            #  STOCK_NUMBER
            {
                "src": "field_720",
                "data-tracker": "field_3467",
            },
            #  CATEGORY
            {
                "src": "field_363",
                "data-tracker": "field_243",
            },
            #  Financial Name
            {
                "src": "field_364",
                "data-tracker": "field_244",
            },
            # Common Name
            {
                "src": "field_914",
                "data-tracker": "field_3617",
            },
            # Modified Date
            {
                "src": "field_374",
                "data-tracker": "field_1229",
            },
            # Modified by
            {
                "src": "field_505_raw",
                "data-tracker": "field_1226",
                "handler": handle_connection,
            },
            #  INVENTORY_TRACKING
            {
                "src": "field_371",
                "data-tracker": "field_1125",
            },
            #  STATUS
            {
                "src": "field_370",
                "data-tracker": "field_1068",
            },
            # UNIT_OF_MEASURE
            {
                "src": "field_377",
                "data-tracker": "field_2420",
            },
            # Object code
            {
                "src": "field_920",
                "data-tracker": "field_3462",
            },
            # Re-Order Threshold
            {
                "src": "field_922",
                "data-tracker": "field_3902",
            },
            # Re-order Turnaround Time
            {
                "src": "field_923",
                "data-tracker": "field_3903",
            },
            # Comment
            {
                "src": "field_924",
                "data-tracker": "field_3905",
            },
        ]
    },
}
