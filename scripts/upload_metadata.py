""" upload knack metadata to S3. metadata is deposited at
's3://atd-knack-{app_name}-{env}/metadata/{app_id}.json'
"""
import argparse
import io
import json
import os

import boto3
import knackpy
import services


def cli_args():
    args = [
        "app-name",
        "env",
    ]
    arg_lib = services.utils.args.args
    parser = argparse.ArgumentParser()

    for arg in args:
        parser.add_argument(f"--{arg}", **arg_lib[arg])

    return parser.parse_args()


def get_env_vars(app_name, env, src="$HOME/.knack/knack.json"):
    home = os.environ["HOME"]
    src = src.replace("$HOME", home)
    with open(src, "r") as fin:
        secrets = json.loads(fin.read())
        return secrets[app_name][env]["app_id"], secrets[app_name][env]["api_key"]


def main():
    args = cli_args()

    app_id, api_key = get_env_vars(args.app_name, args.env)

    metadata = knackpy.api.get_metadata(app_id=app_id)

    payload = json.dumps(metadata).encode()

    client = boto3.client("s3")

    with io.BytesIO(payload) as f:
        response = client.upload_fileobj(
            f, f"atd-knack-{args.app_name}-{args.env}", f"metadata/{app_id}.json",
        )

    if response:
        # todo: understand s3 error responses
        raise Exception("Unknown error.")

    return response


if __name__ == "__main__":
    main()
