import argparse

import arrow
import requests


def cli_args():
    arg = {
        "type": str,
        "required": True,
        "help": "The DAG ID to evaluate.",
    }
    parser = argparse.ArgumentParser()
    parser.add_argument("--dag", **arg)
    return parser.parse_args()


def most_recent_success(dag_runs):
    """ return the execution date of the most recent successful dag run """
    successes = [run for run in dag_runs if run["state"] == "success"]
    if not successes:
        return None
    # sorting in-place is slightly more efficient
    # see: https://docs.python.org/3/howto/sorting.html
    # we're handling ISO-8601 timestamps so we can just evaluate them as strings
    # e.g. '2020-08-23T09:00:00+00:00'
    successes.sort(key=lambda run: run["execution_date"], reverse=True)
    return successes[0]["execution_date"]


def main():
    """ Given a DAG ID, return the most recent successful execution date as a POSIX
    timestamp (without milliseconds)"""
    args = cli_args()
    url = f"https://airflow.austinmobility.io/api/experimental/dags/{args.dag}/dag_runs"
    res = requests.get(url)
    res.raise_for_status()
    last_successful_run_date = most_recent_success(res.json())
    return (
        arrow.get(last_successful_run_date).timestamp
        if last_successful_run_date
        else None
    )


if __name__ == "__main__":
    main()
