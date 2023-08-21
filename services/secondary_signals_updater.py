#!/usr/bin/env python
"""
Update traffic signal records with secondary signal relationships
"""
import argparse
import collections
import os

import knackpy

from config.field_maps import SECONDARY_SIGNALS
from config.knack import CONFIG
import utils

APP_ID = os.getenv("KNACK_APP_ID")
API_KEY = os.getenv("KNACK_API_KEY")


def get_new_prim_signals(signals, field_maps):
    """
    create a dict of primary signals and the secondary signals they control
    data is compiled from the 'primary_signal' field on secondary signals
    this field is maintained by ATD staff via the signals forms in the knack database

    Args:
        signals (TYPE): Description

    Returns:
        TYPE: Description
    """
    signals_with_children = {}

    for signal in signals:

        try:
            #  get id of parent signal
            knack_id = signal[field_maps["PRIMARY_SIGNAL"]][0]["id"]
        except (IndexError, AttributeError):
            #  empty key
            continue

        if knack_id not in signals_with_children:
            #  add entry for parent signal
            signals_with_children[knack_id] = []
        #  add current signal to list of parent's children
        signals_with_children[knack_id].append(signal["id"])

    return signals_with_children


def get_old_prim_signals(signals, field_maps):
    """
    create a dict of primary signals and the secondary signals they control
    data is compiled from the 'secondary_signals' field on primary signals
    this field is populated by this Python service

    Args:
        signals (TYPE): Description

    Returns:
        TYPE: Description
    """
    signals_with_children = {}

    for signal in signals:
        knack_id = signal["id"]

        secondary_signals = []

        try:
            for secondary in signal[field_maps["SECONDARY_SIGNALS"]]:
                secondary_signals.append(secondary["id"])

                signals_with_children[knack_id] = secondary_signals

        except (KeyError, AttributeError):
            continue

    return signals_with_children


def main(args):
    # Parse Arguments
    app_name = args.app_name
    container = args.container
    logger.info(args)

    # Selecting correct config for the view
    config = CONFIG[app_name][container]
    field_mapping = SECONDARY_SIGNALS[app_name][container]

    # Get Signals Knack Data
    kwargs = {"scene": config["scene"], "view": container}
    data = knackpy.api.get(app_id=APP_ID, api_key=API_KEY, **kwargs)

    primary_signals_old = get_old_prim_signals(data, field_mapping)
    primary_signals_new = get_new_prim_signals(data, field_mapping)

    """
    Checking for three separate cases where we need to update Knack
    1. A new secondary signal was added to a primary signal
    2. Secondary signal(s) was/were changed that are attached a primary signal
    3. A secondary signal was removed from a primary signal 
    """

    payload = []

    for signal_id in primary_signals_new:
        """
        identify new and changed primary-secondary relationships
        """
        if signal_id in primary_signals_old:
            new_secondaries = collections.Counter(primary_signals_new[signal_id])
            old_secondaries = collections.Counter(primary_signals_old[signal_id])

            # Checking if things have changed
            if old_secondaries != new_secondaries:
                logger.info(
                    f"Changed primary <> secondary signal relationship detected for signal {signal_id}"
                )
                payload.append(
                    {
                        "id": signal_id,
                        field_mapping["update_field"]: primary_signals_new[signal_id],
                    }
                )

        # Catching new primary-secondary relationship
        else:
            logger.info(
                f"New primary <> secondary signal relationship detected for signal {signal_id}"
            )
            payload.append(
                {
                    "id": signal_id,
                    field_mapping["update_field"]: primary_signals_new[signal_id],
                }
            )

    for signal_id in primary_signals_old:
        """
        identify primary-secondary relationships that have been removed
        """
        if signal_id not in primary_signals_new:
            logger.info(
                f"Deleted primary <> secondary signal relationship detected for signal {signal_id}"
            )
            payload.append({"id": signal_id, field_mapping["update_field"]: []})

    if len(payload) == 0:
        logger.info("No changes detected in Knack, doing nothing.")
        return 0
    logger.info(payload)
    for record in payload:
        res = knackpy.api.record(
            app_id=APP_ID,
            api_key=API_KEY,
            obj=config["object"],
            method="update",
            data=record,
        )

    return len(payload)


if __name__ == "__main__":
    # CLI arguments definition
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--app-name",
        type=str,
        help="str: Name of the Knack App in knack.py config file",
    )

    parser.add_argument(
        "-c",
        "--container",
        type=str,
        help="str: AKA API view that was created for downloading the location data",
    )

    args = parser.parse_args()

    logger = utils.logging.getLogger(__file__)

    main(args)
