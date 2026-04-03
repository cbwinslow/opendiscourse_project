"""Shared utility functions."""

from datetime import datetime, date
from typing import Any, Dict, Optional


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a date string into a date object."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse a datetime string."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str, fmt)
        except (ValueError, TypeError):
            continue
    return None


def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean text for database storage."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    return text


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: list, chunk_size: int):
    """Yield successive chunks from a list."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i : i + chunk_size]
