import re


def format_keys(record):
    """Format Knack record keys by converting to lower case and replacing space
    with underscores. Then, replaces all special characters with underscores."""
    return {
        re.sub(
            r"[^a-z0-9_]+", "", key.lower().replace(" ", "_").replace("-", "_")
        ): val
        for key, val in record.items()
    }
