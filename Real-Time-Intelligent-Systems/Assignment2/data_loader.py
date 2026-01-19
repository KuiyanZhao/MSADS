"""data_loader.py
CSV parsing and MarketDataPoint creation.
Requirement: read market_data.csv using the built-in `csv` module.
Functions:
- read_market_data(path) -> list[MarketDataPoint]  (O(N) time, O(N) space)
- stream_market_data(path) -> iterator[MarketDataPoint] (O(N) time, O(1) extra space)
Notes on space:
- Collecting all ticks in a list is O(N) space.
- Streaming is useful for reducing memory footprint during processing.
"""

from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional
from models import MarketDataPoint


def _parse_timestamp(ts: str) -> datetime:
    ts = ts.strip()
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%y %H:%M:%S",
    ):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized timestamp format: {ts!r}")

def stream_market_data(csv_path: str | Path) -> Iterator[MarketDataPoint]:
    """Yield MarketDataPoint objects from a CSV file.
    Time: O(N)
    Extra space: O(1) (not counting the yielded objects).
    """
    csv_path = Path(csv_path)
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "symbol", "price"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"CSV must have columns {sorted(required)}; got {reader.fieldnames!r}"
            )

        for row in reader:
            yield MarketDataPoint(
                timestamp=_parse_timestamp(row["timestamp"]),
                symbol=row["symbol"].strip(),
                price=float(row["price"]),
            )


def read_market_data(csv_path: str | Path) -> List[MarketDataPoint]:
    """Read the entire CSV into memory as a list.
    Time: O(N)
    Space: O(N)
    """
    return list(stream_market_data(csv_path))
