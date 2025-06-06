import re


def format_keys(record):
    """Rebuild a Knack record by editing the keys by:
    1. Convert to lower case
    2. Replacing space and dashes with underscores.
    3. Replace all special characters with underscores.
    """
    output = {}
    for key, val in record.items():
        key = key.lower()
        key = key.replace(" ", "_")
        key = key.replace("-", "_")
        key = re.sub(r"[^a-z0-9_]+", "", key)
        output[key] = val
    return output
