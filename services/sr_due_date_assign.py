import argparse
import logging
import os
import sys
import requests

import arrow
from config.sr_due_date import CONFIG
import utils
import knackpy


APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")


def main(args):
    logging.info(args.app_name)
    # team_name = args.team


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--app-name",
        type=str,
        help="str: Name of the Knack App, data_tracker or signs_markings",
    )

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    args = parser.parse_args()
    main(args)
