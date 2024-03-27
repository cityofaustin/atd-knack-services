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


def handle_multiple_choice(value):
    """
    Return a string of comma-separated values from a multi-choice field type

    Input:
        value (list)
    Output:
        string of comma-separated values of input list
    """
    if not value:
        return None
    if len(value) == 1:
        return str(value[0])
    return ", ".join(str(v) for v in value)


def handle_strip(value):
    try:
        return value.strip()
    except AttributeError:
        return value


def handle_no_choice_to_empty_string(value):
    """
    Useful for going from a single choice field to a short text datatype.
    If no option is picked for a single choice the API will return None.
    The short text field will return an empty string.
    """
    if not value:
        return ""


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
            # Council district
            {
                "src": "field_189_raw",
                "smart-mobility": "field_385",
                "handler": handle_multiple_choice,
            },
            # Signal Name
            {
                "src": "field_1058",
                "smart-mobility": "field_386",
            },
            # Signal Engineer Area
            {
                "src": "field_188_raw",
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
    "hr-manager": {
        "view_684": [
            # Name
            {
                "src": "field_17_raw",
                "tpw-hire": "field_160_raw",
            },
            # Employee ID
            {"src": "field_99", "tpw-hire": "field_161", "primary_key": True},
            # Email
            {
                "src": "field_18_raw",
                "tpw-hire": "field_166_raw",
            },
            # Position Number
            {
                "src": "field_248",
                "tpw-hire": "field_162",
            },
            # Department
            {
                "src": "field_137",
                "tpw-hire": "field_167",
            },
            # Division
            {
                "src": "field_97",
                "tpw-hire": "field_163",
            },
            # Class
            {
                "src": "field_95",
                "tpw-hire": "field_164",
            },
            # Class Description
            {
                "src": "field_251",
                "tpw-hire": "field_165",
                "handler": handle_no_choice_to_empty_string,
            },
        ]
    },
}

SECONDARY_SIGNALS = {
    "data-tracker": {
        "view_197": {
            "SECONDARY_SIGNALS": "field_1329_raw",
            "PRIMARY_SIGNAL": "field_1121_raw",
            "update_field": "field_1329",
        }
    }
}
