"""CSV parser for FEC bulk data and other CSV files."""

import csv
from typing import Dict, Generator, List


def read_csv_file(file_path: str, delimiter: str = ",") -> List[Dict[str, str]]:
    """Read entire CSV file into list of dicts."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def stream_csv_file(file_path: str, delimiter: str = ",") -> Generator[Dict[str, str], None, None]:
    """Stream CSV file row by row."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            yield row
