import os
import sodapy


def socrata_formatter(value):
    if not value:
        return value
    lat = value.get("latitude")
    lon = value.get("longitude")
    return f"({lat}, {lon})" if lat and lon else None


def upsert(*, resource_id, payload, host="data.austintexas.gov"):
    """Just a sodapy wrapper"""
    client = sodapy.Socrata(
        host,
        None,
        username=os.environ["SOCRATA_USERNAME"],
        password=os.environ["SOCRATA_PASSWORD"],
    )
    return client.upsert(resource_id, payload)
