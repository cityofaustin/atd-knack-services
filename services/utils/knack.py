import arrow


def socrata_formatter_location(value):
    if not value:
        return value
    return f"({value['longitude']}, { value['latitude']})"


def socrata_formatter_point(value):
    if not value:
        return value

    return {
        "type": "Point",
        "coordinates": [float(value["longitude"]), float(value["latitude"])],
    }


def date_filter_on_or_after(timestamp, date_field, tzinfo="US/Central"):
    """Return a Knack filter to retrieve records on or after a given date field/value.
    If timestamp is None, defaults to 01/01/1970.

    You should know:
    - Knack ignores time when querying by date. So we drop it when formatting the
        filters to avoid any confusion there.
    - Again, Knack ignores time, so the "is" operator matches on calendar date. And
        "is after" matches any calendar dates following a given date.
    - The Knack API seems to be capable of parsing quite a few date formats, but we use
        `MM/DD/YYYY`
    - Knack is completely timezone naive. If you provide a date, it assumes the date
    is referencing the same locality to which the Knack app is configured.
    """
    date_str = timestamp or 0

    date_str = (
        arrow.get(timestamp).to(tzinfo).format("MM/DD/YYYY")
        if timestamp
        else "01/01/1970"
    )

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
