def format_keys(record):
    """Format Knack record keys by converting to lower case and replacing space
    with underscores"""
    return {key.lower().replace(" ", "_"): val for key, val in record.items()}
