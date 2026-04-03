"""JSON parser for API responses."""

import json
from typing import Any, Dict, List, Optional


def parse_json_string(json_string: str) -> Any:
    """Parse JSON string."""
    return json.loads(json_string)


def parse_json_file(file_path: str) -> Any:
    """Parse JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def extract_nested(data: Dict, *keys: str, default: Any = None) -> Any:
    """Safely extract nested dictionary values."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list) and isinstance(key, int):
            try:
                current = current[key]
            except IndexError:
                return default
        else:
            return default
    return current


def flatten_list_of_dicts(data: Dict, list_key: str) -> List[Dict]:
    """Extract a list of dicts from a nested response."""
    result = extract_nested(data, list_key)
    if isinstance(result, list):
        return result
    return []
