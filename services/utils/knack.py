import json
import os
import pathlib

import arrow


def set_env(
    app_name,
    env,
    config_path=".knack/config",
    var_names=["app_id", "api_key"],
):
    # check if we're already good to go
    print(os.environ)
    if all([name in os.environ for name in var_names]):
        return
    
    # attempt to load from ~/.knack/config
    home = str(pathlib.Path.home())
    path = os.path.join(home, config_path)

    if not os.path.exists(path):
        raise EnvironmentError(
            f"Unable to find Knack environmental variables at {path}"
        )

    with open(path, "r") as fin:
        try:
            env_config = json.loads(fin.read())

            for name in var_names:
                os.environ[name] = env_config[app_name][env][name]

        except (KeyError, json.decoder.JSONDecodeError):
            raise IOError(f"Invalid Knack environment file: {path}")
    breakpoint()


def date_filter_on_or_after(timestamp, date_field):
    """Return a Knack filter to retrieve records on or after a given date field/value.
    If timestamp is None, defaults to 01/01/1970.

    Note that time is ignored/not supported by Knack API"""
    #  knack date filter requires MM/DD/YYYY
    date_str = timestamp or 0
    date_str = arrow.get(timestamp).format("MM/DD/YYYY") if timestamp else "01/01/1970"

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
