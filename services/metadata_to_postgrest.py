#!/usr/bin/env python
"""Upload Knack metadata to Postgrest"""
import os

import knackpy
from pypgrest import Postgrest


def main():
    APP_ID = os.getenv("KNACK_APP_ID")
    PGREST_JWT = os.getenv("PGREST_JWT")
    PGREST_ENDPOINT = os.getenv("PGREST_ENDPOINT")
    metadata = knackpy.api.get_metadata(app_id=APP_ID)
    client = Postgrest(PGREST_ENDPOINT, token=PGREST_JWT)
    client.upsert(
        resource="knack_metadata", data={"app_id": APP_ID, "metadata": metadata}
    )


if __name__ == "__main__":
    main()
