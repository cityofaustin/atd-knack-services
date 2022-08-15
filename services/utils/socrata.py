from datetime import datetime
import os

import arrow
import sodapy


def get_field_type_by_field_name(field_name, metadata):
    matched = [
        c["dataTypeName"] for c in metadata["columns"] if c["fieldName"] == field_name
    ]
    try:
        return matched[0]
    except IndexError:
        raise ValueError(f"Unable to find field {field_name}")


def get_floating_timestamp_fields(resource_id, metadata):
    return [
        c["fieldName"]
        for c in metadata["columns"]
        if c["dataTypeName"] == "calendar_date"
    ]


def append_current_timestamp(
    records, key, tzinfo="US/Central", format_="YYYY-MM-DDTHH:mm:ss"
):
    """Appends an ISO-8601 timestamp to each record.

    The timestamp is created in US/Central time without the tz string. This
    is unfortunately the socrata way.

    Args:
        records (list): A list of record dicts
        key (str): The key which will be added to each record dict with the timestamp value
        format_ (str): The arrow formatting token string

    Returns:
        None: the records are updated in place.
    """
    now = arrow.now().to(tzinfo).format(format_)
    for record in records:
        record[key] = now


def get_client(host="data.austintexas.gov", timeout=30):
    SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")
    SOCRATA_API_KEY_ID = os.getenv("SOCRATA_API_KEY_ID")
    SOCRATA_API_KEY_SECRET = os.getenv("SOCRATA_API_KEY_SECRET")

    return sodapy.Socrata(
        host,
        SOCRATA_APP_TOKEN,
        username=SOCRATA_API_KEY_ID,
        password=SOCRATA_API_KEY_SECRET,
        timeout=timeout,
    )


def publish(*, method, resource_id, payload, client):
    """Just a sodapy wrapper that chunks payloads"""

    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    for chunk in chunks(payload, 1000):
        if method == "replace":
            # replace the dataset with first chunk
            # subsequent chunks will be upserted
            client.replace(resource_id, chunk)
            method = "upsert"
        else:
            client.upsert(resource_id, chunk)
