""" Download knack app metadata json from S3 """
import json
import boto3


def download(app_name, app_id, env):
    s3 = boto3.resource("s3")
    bucket_name = f"atd-knack-{app_name}-{env}"
    f = f"metadata/{app_id}.json"
    response = s3.Object(bucket_name, f).get()
    return json.loads(response["Body"].read())
