import arrow
from dateutil import tz


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
            "coordinates": [[float(v["longitude"]), float(v["latitude"])] for v in value],
        }
    except ValueError:
        return None


def local_timestamp(tzname="US/Central"):
    """
    Create a "local" timestamp (in milliseconds), ie local time represented as a unix timestamp.
    Used to set datetimes when writing Knack records, because Knack assumes input
    time values are in local time.
    """
    return arrow.now(tzname).replace(tzinfo=tz.gettz("UTC")).int_timestamp * 1000


def date_filter_on_or_after(timestamp, date_field, tzinfo="US/Central", use_time=False):
    """Return a Knack filter to retrieve records on or after a given date field/value.

    Parameters:
        timestamp (str): string formatted datetime (assumed UTC) 'YYYY-MM-DD HH:MM'
        date_field (str): field id of the date field you are filtering in knack. Formatted as : field_123
        tzinfo (str): string of the timezone of the provided Knack App, timestamp will be converted to this.
        use_time (bool): if True, will use date and time filtering, if not will use only date filtering.

    Returns:
        filter (dict): A dictionary formatted to work with Knack's API or KnackPy's .get() function
    """
    if not timestamp or not date_field:
        return None

    if use_time:
        date_str = arrow.get(timestamp).to(tzinfo).format("MM/DD/YYYY HH:mm")
    else:
        date_str = arrow.get(timestamp).to(tzinfo).format("MM/DD/YYYY")

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
