import argparse
import json
import os

import knackpy
import services
import sodapy


def cli_args():
    args = ["app-name", "container", "env", "date"]
    arg_lib = services.utils.args.args
    parser = argparse.ArgumentParser()

    for arg in args:
        parser.add_argument(f"--{arg}", **arg_lib[arg])

    return parser.parse_args()


def set_env_vars(app_name, env, src="$HOME/.knack/knack.json"):
    home = os.environ["HOME"]
    src = src.replace("$HOME", home)

    with open(src, "r") as fin:
        secrets = json.loads(fin.read())
        os.environ["KNACK_APP_ID"] = secrets[app_name][env]["app_id"]
        os.environ["SOCRATA_USERNAME"] = secrets["socrata"]["username"]
        os.environ["SOCRATA_PASSWORD"] = secrets["socrata"]["password"]


def get_config(app_name, container):
    return services.config.config.config.get(app_name).get(container)


def lower_case_keys(records):
    return [{key.lower(): val for key, val in record.items()} for record in records]


def bools_to_strings(records):
    for record in records:
        for k, v in record.items():
            if isinstance(v, bool):
                record[k] = str(v)
    return records


def socrata_formatter(value):
    if not value:
        return value

    lat = value.get("latitude")
    lon = value.get("longitude")
    return f"({lat}, {lon})" if lat and lon else None


def patch_formatters(app, location_fields):
    """replace knackpy's default address fomatter with our custom socrata formatter"""
    for key in location_fields:
        for field_def in app.field_defs:
            if field_def.key == key:
                field_def.formatter = socrata_formatter
                break
    return app


def main():
    args = cli_args()

    config = get_config(args.app_name, args.container)

    set_env_vars(args.app_name, args.env)

    bucket_name = f"atd-knack-{args.app_name}-{args.env}"

    records_raw = services.s3.download.download(
        bucket_name, args.container, date_filter=args.date, as_dicts=True
    )

    if not records_raw:
        return 0

    metadata_knack = services.s3.get_metadata.download(
        args.app_name, os.environ["KNACK_APP_ID"], args.env
    )

    app = knackpy.App(app_id=os.environ["KNACK_APP_ID"], metadata=metadata_knack)

    location_fields = config.get("location_fields")

    app = patch_formatters(app, location_fields)

    app.data[args.container] = records_raw

    records = app.get(args.container)

    payload = [record.format() for record in records]

    payload = lower_case_keys(payload)

    payload = bools_to_strings(payload)

    client = sodapy.Socrata(
        "data.austintexas.gov",
        None,
        username=os.environ["SOCRATA_USERNAME"],
        password=os.environ["SOCRATA_PASSWORD"],
    )

    return client.upsert(config.get("socrata_resource_id"), payload)


if __name__ == "__main__":
    main()
