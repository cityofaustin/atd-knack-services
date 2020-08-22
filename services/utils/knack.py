import arrow


def date_filter_on_or_after(date_str, date_field):
    """Return a Knack filter to retrieve records on or after a given date field/value.
    If date_str is None, defaults to 01/01/1970.

    Note that time is ignored/not supported by Knack API"""

    #  knack date filter requires MM/DD/YYYY
    date_str = arrow.get(date_str).format("MM/DD/YYYY") if date_str else "01/01/1970"

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
