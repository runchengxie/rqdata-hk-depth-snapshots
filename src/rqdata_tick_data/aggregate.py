"""Daily aggregation for raw HK tick-depth snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rqdata_tick_data.storage import (
    atomic_write_parquet,
    load_parquet_parts,
    metadata_path,
    write_json,
)

DAILY_METRIC_COLUMNS = (
    "tick_count",
    "quote_coverage_ratio",
    "bad_quote_ratio",
    "spread_bps_p50",
    "spread_bps_p90",
    "depth1_notional_p50",
    "depth5_notional_p50",
    "depth10_notional_p50",
    "imbalance1_p50",
    "imbalance5_p50",
    "open_30m_vwap",
    "full_day_tick_vwap",
    "open_to_tick_vwap_bps",
)


def _num(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _has(group: pd.DataFrame, columns: list[str]) -> bool:
    return all(column in group.columns for column in columns)


def spread_bps(group: pd.DataFrame) -> pd.Series:
    if not _has(group, ["a1", "b1"]):
        return pd.Series(dtype="float64")
    ask = _num(group, "a1")
    bid = _num(group, "b1")
    valid = (ask > 0) & (bid > 0) & (ask >= bid)
    mid = (ask + bid) / 2
    return ((ask - bid) / mid * 10000).where(valid)


def depth_notional(group: pd.DataFrame, levels: int) -> pd.Series:
    required = []
    for level in range(1, levels + 1):
        required.extend([f"a{level}", f"a{level}_v", f"b{level}", f"b{level}_v"])
    if not _has(group, required):
        return pd.Series(dtype="float64")
    total = pd.Series(0.0, index=group.index)
    for level in range(1, levels + 1):
        total = total + _num(group, f"a{level}") * _num(group, f"a{level}_v")
        total = total + _num(group, f"b{level}") * _num(group, f"b{level}_v")
    return total


def imbalance(group: pd.DataFrame, levels: int) -> pd.Series:
    required = []
    for level in range(1, levels + 1):
        required.extend([f"a{level}", f"a{level}_v", f"b{level}", f"b{level}_v"])
    if not _has(group, required):
        return pd.Series(dtype="float64")
    ask = pd.Series(0.0, index=group.index)
    bid = pd.Series(0.0, index=group.index)
    for level in range(1, levels + 1):
        ask = ask + _num(group, f"a{level}") * _num(group, f"a{level}_v")
        bid = bid + _num(group, f"b{level}") * _num(group, f"b{level}_v")
    denom = ask + bid
    return ((bid - ask) / denom).where(denom > 0)


def _incremental(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    delta = numeric.diff()
    if not numeric.empty:
        delta.iloc[0] = numeric.iloc[0]
    return delta.where(delta >= 0)


def _vwap(group: pd.DataFrame) -> float | None:
    if not _has(group, ["volume", "total_turnover"]):
        return None
    ordered = group.sort_values("datetime") if "datetime" in group.columns else group
    volume = _incremental(ordered["volume"])
    turnover = _incremental(ordered["total_turnover"])
    valid = (volume > 0) & (turnover >= 0)
    volume_sum = volume[valid].sum()
    if not volume_sum:
        return None
    return float(turnover[valid].sum() / volume_sum)


def _open_30m(group: pd.DataFrame) -> pd.DataFrame:
    if "datetime" not in group.columns:
        return group.iloc[0:0]
    ordered = group.copy()
    ordered["datetime"] = pd.to_datetime(ordered["datetime"], errors="coerce")
    start = ordered["datetime"].min()
    if pd.isna(start):
        return ordered.iloc[0:0]
    return ordered.loc[ordered["datetime"] <= start + pd.Timedelta(minutes=30)]


def aggregate_group(group: pd.DataFrame) -> dict[str, Any]:
    row: dict[str, Any] = {
        "order_book_id": group["order_book_id"].iloc[0],
        "trading_date": group["trading_date"].iloc[0],
        "tick_count": int(len(group)),
    }

    if _has(group, ["a1", "b1"]):
        ask = _num(group, "a1")
        bid = _num(group, "b1")
        positive = (ask > 0) & (bid > 0)
        invalid = positive & (ask < bid)
        row["quote_coverage_ratio"] = float(positive.mean())
        row["bad_quote_ratio"] = float((~positive | invalid).mean())
    else:
        row["quote_coverage_ratio"] = pd.NA
        row["bad_quote_ratio"] = pd.NA

    spread = spread_bps(group)
    row["spread_bps_p50"] = float(spread.quantile(0.50)) if not spread.dropna().empty else pd.NA
    row["spread_bps_p90"] = float(spread.quantile(0.90)) if not spread.dropna().empty else pd.NA

    for levels in (1, 5, 10):
        depth = depth_notional(group, levels)
        key = f"depth{levels}_notional_p50"
        row[key] = float(depth.quantile(0.50)) if not depth.dropna().empty else pd.NA

    for levels in (1, 5):
        series = imbalance(group, levels)
        key = f"imbalance{levels}_p50"
        row[key] = float(series.quantile(0.50)) if not series.dropna().empty else pd.NA

    full_vwap = _vwap(group)
    open_vwap = _vwap(_open_30m(group))
    row["open_30m_vwap"] = open_vwap if open_vwap is not None else pd.NA
    row["full_day_tick_vwap"] = full_vwap if full_vwap is not None else pd.NA
    if open_vwap is not None and full_vwap:
        row["open_to_tick_vwap_bps"] = float((open_vwap / full_vwap - 1) * 10000)
    else:
        row["open_to_tick_vwap_bps"] = pd.NA

    return row


def unavailable_metrics(df: pd.DataFrame) -> dict[str, list[str]]:
    requirements = {
        "spread_bps_p50": ["a1", "b1"],
        "spread_bps_p90": ["a1", "b1"],
        "depth1_notional_p50": ["a1", "a1_v", "b1", "b1_v"],
        "depth5_notional_p50": [
            *(f"a{i}" for i in range(1, 6)),
            *(f"a{i}_v" for i in range(1, 6)),
            *(f"b{i}" for i in range(1, 6)),
            *(f"b{i}_v" for i in range(1, 6)),
        ],
        "depth10_notional_p50": [
            *(f"a{i}" for i in range(1, 11)),
            *(f"a{i}_v" for i in range(1, 11)),
            *(f"b{i}" for i in range(1, 11)),
            *(f"b{i}_v" for i in range(1, 11)),
        ],
        "imbalance1_p50": ["a1", "a1_v", "b1", "b1_v"],
        "imbalance5_p50": [
            *(f"a{i}" for i in range(1, 6)),
            *(f"a{i}_v" for i in range(1, 6)),
            *(f"b{i}" for i in range(1, 6)),
            *(f"b{i}_v" for i in range(1, 6)),
        ],
        "open_30m_vwap": ["datetime", "volume", "total_turnover"],
        "full_day_tick_vwap": ["volume", "total_turnover"],
        "open_to_tick_vwap_bps": ["datetime", "volume", "total_turnover"],
    }
    missing: dict[str, list[str]] = {}
    for metric, columns in requirements.items():
        absent = [column for column in columns if column not in df.columns]
        if absent:
            missing[metric] = absent
    return missing


def aggregate_daily_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        columns = ["order_book_id", "trading_date", *DAILY_METRIC_COLUMNS]
        return pd.DataFrame(columns=columns)
    required = {"order_book_id", "trading_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required aggregate columns: {sorted(missing)}")
    rows = [
        aggregate_group(group)
        for _, group in df.groupby(["order_book_id", "trading_date"], sort=True, dropna=False)
    ]
    out = pd.DataFrame(rows)
    for column in DAILY_METRIC_COLUMNS:
        if column not in out.columns:
            out[column] = pd.NA
    return out[["order_book_id", "trading_date", *DAILY_METRIC_COLUMNS]]


def write_daily_aggregate(
    input_root: str | Path,
    output_path: str | Path,
    meta_output: str | Path | None = None,
    schema_version: str = "tick_depth_daily.v1",
) -> dict[str, Any]:
    df = load_parquet_parts(input_root)
    aggregate = aggregate_daily_frame(df)
    output = atomic_write_parquet(aggregate, output_path)
    unavailable = unavailable_metrics(df)
    metadata = {
        "kind": "aggregate_daily",
        "schema_version": schema_version,
        "source_path": str(input_root),
        "output_path": str(output),
        "source_rows": int(len(df)),
        "rows": int(len(aggregate)),
        "unavailable_metrics": sorted(unavailable),
        "missing_source_fields": unavailable,
    }
    meta_path = (
        Path(meta_output) if meta_output else metadata_path(Path(output).parent, "aggregate_daily")
    )
    write_json(meta_path, metadata)
    metadata["metadata_path"] = str(meta_path)
    return metadata
