"""Symbol and date parsing helpers."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta
from pathlib import Path


def _append_unique(items: list[str], value: str) -> None:
    value = value.strip()
    if value and value not in items:
        items.append(value)


def parse_symbols(symbols: str | None = None, symbols_file: str | Path | None = None) -> list[str]:
    """Parse order book ids from CLI text and/or a file."""
    parsed: list[str] = []
    if symbols:
        for chunk in symbols.replace(",", " ").split():
            _append_unique(parsed, chunk)
    if symbols_file:
        path = Path(symbols_file)
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for chunk in stripped.replace(",", " ").split():
                _append_unique(parsed, chunk)
    if not parsed:
        raise ValueError("At least one symbol is required.")
    return parsed


def parse_date(value: str | date | datetime) -> date:
    """Parse YYYYMMDD or ISO date strings."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date {value!r}; expected YYYYMMDD or YYYY-MM-DD.")


def format_date(value: str | date | datetime) -> str:
    """Format a date as YYYYMMDD."""
    return parse_date(value).strftime("%Y%m%d")


def iter_dates(start_date: str | date | datetime, end_date: str | date | datetime) -> Iterator[str]:
    """Yield calendar dates in deterministic inclusive order as YYYYMMDD."""
    start = parse_date(start_date)
    end = parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be on or before end_date.")
    current = start
    while current <= end:
        yield current.strftime("%Y%m%d")
        current += timedelta(days=1)
