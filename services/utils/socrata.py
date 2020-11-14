import os

import arrow
import sodapy

def get_floating_timestamp_fields(client, resource_id):
    metadata = client.get_metadata(resource_id)
    return [c["fieldName"] for c in metadata["columns"] if c["dataTypeName"] == "calendar_date"]

def handle_floating_timestamps(data, floating_timestamp_fields):
    """ Socrata's fixed timestamp dataType does not allow tz info :( 
        Alternatively, once can setup a transform to convert the datatype to a fixed
        timestamp: https://dev.socrata.com/docs/transforms/to_fixed_timestamp.html
    """
    for row in data:
        for field in floating_timestamp_fields:
            dt = row.get(field)
            if not dt:
                continue
            row[field] = arrow.get(dt).format("YYYY-MM-DDTHH:MM:SS")
    return
    
def socrata_formatter_location(value):
    if not value:
        return value
    lat = value.get("latitude")
    lon = value.get("longitude")
    return f"({lat}, {lon})" if lat and lon else None


def publish(*, method, resource_id, payload, host="data.austintexas.gov"):
    """Just a sodapy wrapper that chunks payloads"""
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
    SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
    SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")
    client = sodapy.Socrata(
        host,
        SOCRATA_APP_TOKEN,
        username=SOCRATA_API_KEY_ID,
        password=SOCRATA_API_KEY_SECRET,
    )
    floating_timestamp_fields = get_floating_timestamp_fields(client, resource_id)
    handle_floating_timestamps(payload, floating_timestamp_fields)

    for chunk in chunks(payload, 5000):
        if method == "replace":
            # replace the dataset with first chunk
            # subsequent chunks will be upserted
            client.replace(resource_id, chunk)
            method = "upsert"
        else:
            client.upsert(resource_id, chunk)