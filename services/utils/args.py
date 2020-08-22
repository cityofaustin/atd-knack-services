""" Common client args for interfacing with this API """
args = {
    "app-name": {
        "type": str,
        "required": True,
        "help": "The name of the app. must match an entry in secrets.py",
    },
    "container": {
        "type": str,
        "required": True,
        "help": "The Knack object ID or view ID to process",
    },
    "env": {
        "type": str,
        "required": True,
        "choices": ["dev", "prod"],
        "help": "The app environment. Choose dev or prod",
    },
    "date": {
        "type": int,
        "required": False,
        "help": "A unix timestamp with millesconds which will be used to query records >= date",  # noqa
    },
}
