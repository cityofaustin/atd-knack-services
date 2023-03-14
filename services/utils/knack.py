import arrow


def get_metadata(client, app_id):
    """Download knack metadata from postgrest. Need this in order to format Knack record values
        with Knackpy.

    Args:
        client (pypgrest.Postgrest): a postgrest client
        app_id (str): the Knack app's ID

    Returns:
        dict: the app's metadata
    """
    results = client.select(
        resource="knack_metadata",
        params={"app_id": f"eq.{app_id}", "limit": 1},
        pagination=False,
    )
    if results:
        return results[0]["metadata"]
    return None


def socrata_formatter_location(value):
    if not value:
        return value
    return f"({ value['latitude']}, {value['longitude']})"


def socrata_formatter_point(value):
    if not value:
        return value

    return {
        "type": "Point",
        "coordinates": [float(value["longitude"]), float(value["latitude"])],
    }


def socrata_formatter_multipoint(value):
    # Location type: Multipoint
    # https://dev.socrata.com/docs/datatypes/multipoint.html#,
    if not value:
        return value

    try:
        return {
            "type": "MultiPoint",
            "coordinates": [
                [float(v["longitude"]), float(v["latitude"])] for v in value
            ],
        }
    except ValueError:
        return None


def date_filter_on_or_after(timestamp, date_field, tzinfo="US/Central"):
    """Return a Knack filter to retrieve records on or after a given date field/value.

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
    if not timestamp or not date_field:
        return None

    date_str = arrow.get(timestamp).to(tzinfo).format("MM/DD/YYYY")

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
