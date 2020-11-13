import os
import sodapy


def socrata_formatter(value):
    if not value:
        return value
    lat = value.get("latitude")
    lon = value.get("longitude")
    return f"({lat}, {lon})" if lat and lon else None


def publish(*, method, resource_id, payload, host="data.austintexas.gov"):
    """Just a sodapy wrapper"""
    SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
    SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
    SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")
    client = sodapy.Socrata(
        host,
        SOCRATA_APP_TOKEN,
        username=SOCRATA_API_KEY_ID,
        password=SOCRATA_API_KEY_SECRET,
    )
    if method == "upsert":
        return client.upsert(resource_id, payload)
    elif method == "replace":
        return client.replace(resource_id, payload)

    raise ValueError(f"Unknown 'method' value provided: {method}")
