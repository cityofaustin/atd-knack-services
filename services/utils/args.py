import argparse

# Common client arg definitions for interfacing with this API
ARG_DEFS = {
    "app-name": {
        "flag": "-a",
        "type": str,
        "required": True,
        "help": "The name of the app. Must match an entry in ~/.knack/config",
    },
    "container": {
        "flag": "-c",
        "type": str,
        "required": True,
        "help": "The Knack object ID or view ID to process",
    },
    "env": {
        "flag": "-e",
        "type": str,
        "required": True,
        "choices": ["dev", "prod"],
        "help": "The app environment. Choose dev or prod",
    },
    "date": {
        "flag": "-d",
        "type": str,
        "required": False,
        "help": "An ISO 8601-compliant date string which will be used to query records",
    },
    "app-name-dest": {
        "flag": "-dest",
        "type": str,
        "required": False,
        "help": "The name of the destination Knack app. Required for publishing between Knack apps."
    },
}


def cli_args(arg_names):
    """Helper for creating an arg parser

    Args:
        arg_names (list): A list of argument names. Each arg name must be defined in
            ARG_DEFS, above.

    Returns:
        argparse.ArgumentParser: An argument parser.
    """
    parser = argparse.ArgumentParser()
    for name in arg_names:
        flag = ARG_DEFS[name].pop("flag", None)
        parser.add_argument(f"--{name}", flag, **ARG_DEFS[name])
    return parser.parse_args()
