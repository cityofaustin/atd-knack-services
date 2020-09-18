import json
import os
import pathlib

import arrow


def set_env(
    app_name, env, config_path=".knack/credentials", var_names=["app_id", "api_key"],
):
    # check if we're already good to go
    if all([name in os.environ for name in var_names]):
        return

    # attempt to load from ~/.knack/credentials
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


def date_filter_on_or_after(timestamp, date_field, tzinfo="US/Central"):
    """Return a Knack filter to retrieve records on or after a given date field/value.
    If timestamp is None, defaults to 01/01/1970.

    You should know:
    - Knack ignores time when querying by date. So we drop it when formatting the
        filters to avoid any confusion there.
    - Again, Knack ignores time, so the "is" operator matches on calendar date. And
        "is after" matches any calendar dates following a given date.
    - The Knack API seems to be capable of parsing quite a few date formats, but we use
        `MM/DD/YYYY`
    - Knack is completely timezone naive. If you provide a date, it assumes the date
    is referencing the same locality to which the Knack app is configured.
    """
    date_str = timestamp or 0

    date_str = (
        arrow.get(timestamp).to(tzinfo).format("MM/DD/YYYY")
        if timestamp
        else "01/01/1970"
    )

    return {
        "match": "or",
        "rules": [
            {"field": f"{date_field}", "operator": "is", "value": f"{date_str}"},
            {"field": f"{date_field}", "operator": "is after", "value": f"{date_str}"},
        ],
    }
