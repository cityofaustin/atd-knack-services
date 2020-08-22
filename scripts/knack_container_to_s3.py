""" download Knack records and upload to S3 """
import argparse
import io
import json
import os

import knackpy
import services

# e.g. python upload_to_s3.py -a data-tracker -c object_11 -e prod


def get_env_vars(app_name, env, src="$HOME/.knack/knack.json"):
    home = os.environ["HOME"]
    src = src.replace("$HOME", home)
    with open(src, "r") as fin:
        secrets = json.loads(fin.read())
        return secrets[app_name][env]["app_id"], secrets[app_name][env]["api_key"]


def get_config(app_name, container):
    return services.config.config.config.get(app_name).get(container)


def cli_args():
    args = ["app-name", "container", "env", "date"]
    arg_lib = services.utils.args.args
    parser = argparse.ArgumentParser()

    for arg in args:
        parser.add_argument(f"--{arg}", **arg_lib[arg])

    return parser.parse_args()


def file_name(record, container):
    return f"{container}/{record['id']}.json"


def fileobj(record):
    return io.BytesIO(json.dumps(record).encode())


def build_record_packages(records, app_name, env, container):
    bucket_name = f"atd-knack-{app_name}-{env}"

    return [
        services.s3.upload.RecordPackage(
            fileobj=fileobj(record),
            bucket_name=bucket_name,
            file_name=file_name(record, container),
        )
        for record in records
    ]


def container_kwargs(container, config, obj=None, scene=None, view=None):
    """Knack API requires either an object key or a scene and view key"""
    if "object_" in container:
        obj = container
    else:
        scene = config.get("scene")
        view = container
    return {"obj": obj, "scene": scene, "view": view}


def main():
    args = cli_args()

    app_id, api_key = get_env_vars(args.app_name, args.env)

    config = get_config(args.app_name, args.container)

    modified_date_field = config["modified_date_field"]

    filters = services.utils.knack.date_filter_on_or_after(
        args.date, modified_date_field
    )

    kwargs = container_kwargs(args.container, config)

    records = knackpy.api.get(
        app_id=app_id, api_key=api_key, filters=filters, **kwargs,
    )

    record_packages = build_record_packages(
        records, args.app_name, args.env, args.container
    )

    results = services.s3.upload.upload(record_packages)

    return results


if __name__ == "__main__":
    main()
