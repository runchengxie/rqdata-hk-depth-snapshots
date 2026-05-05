"""Health checks for raw tick-depth parquet parts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rqdata_tick_data.storage import load_parquet_parts, metadata_path, write_json

REQUIRED_RAW_COLUMNS = ("order_book_id", "datetime")


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def inspect_raw_health(input_root: str | Path) -> dict[str, Any]:
    df = load_parquet_parts(input_root)
    report: dict[str, Any] = {
        "input_root": str(input_root),
        "row_count": int(len(df)),
        "symbol_count": 0,
        "date_count": 0,
        "timestamp_start": None,
        "timestamp_end": None,
        "missing_required_columns": [],
        "field_missing_rates": {},
        "duplicate_row_count": 0,
        "duplicate_key_count": 0,
        "invalid_best_spread_count": 0,
        "invalid_best_spread_groups": [],
        "quote_coverage_ratio": None,
        "bad_quote_ratio": None,
        "negative_volume_count": None,
        "negative_turnover_count": None,
        "volume_decrease_count": None,
        "turnover_decrease_count": None,
        "warnings": [],
        "failures": [],
        "status": "pass",
    }

    if df.empty:
        report["failures"].append("empty_dataset")
        report["status"] = "fail"
        return report

    missing = [col for col in REQUIRED_RAW_COLUMNS if col not in df.columns]
    report["missing_required_columns"] = missing
    if missing:
        report["failures"].append("missing_required_columns")
        report["status"] = "fail"

    if "order_book_id" in df.columns:
        report["symbol_count"] = int(df["order_book_id"].nunique(dropna=True))
    if "trading_date" in df.columns:
        report["date_count"] = int(df["trading_date"].nunique(dropna=True))

    if "datetime" in df.columns:
        timestamps = pd.to_datetime(df["datetime"], errors="coerce")
        parse_failures = int(timestamps.isna().sum())
        report["timestamp_parse_failure_count"] = parse_failures
        if parse_failures:
            report["warnings"].append("timestamp_parse_failures")
        if timestamps.notna().any():
            report["timestamp_start"] = timestamps.min().isoformat()
            report["timestamp_end"] = timestamps.max().isoformat()

    report["field_missing_rates"] = {
        str(column): float(rate) for column, rate in df.isna().mean(numeric_only=False).items()
    }

    if all(col in df.columns for col in REQUIRED_RAW_COLUMNS):
        duplicated = df.duplicated(["order_book_id", "datetime"], keep=False)
        report["duplicate_row_count"] = int(duplicated.sum())
        if duplicated.any():
            report["duplicate_key_count"] = int(
                df.loc[duplicated, ["order_book_id", "datetime"]].drop_duplicates().shape[0]
            )
            report["warnings"].append("duplicate_symbol_timestamp_rows")

    if {"a1", "b1"}.issubset(df.columns):
        a1 = _numeric(df, "a1")
        b1 = _numeric(df, "b1")
        positive = (a1 > 0) & (b1 > 0)
        invalid_spread = positive & (a1 < b1)
        report["quote_coverage_ratio"] = float(positive.mean())
        report["bad_quote_ratio"] = float((~positive | invalid_spread).mean())
        report["invalid_best_spread_count"] = int(invalid_spread.sum())
        if invalid_spread.any():
            group_cols = [col for col in ("order_book_id", "trading_date") if col in df.columns]
            if group_cols:
                groups = (
                    df.loc[invalid_spread, group_cols].drop_duplicates().head(20).to_dict("records")
                )
                report["invalid_best_spread_groups"] = groups
            report["warnings"].append("invalid_best_quote_spread")

    group_cols = [col for col in ("order_book_id", "trading_date") if col in df.columns]
    sort_cols = [col for col in (*group_cols, "datetime") if col in df.columns]
    checked = df.sort_values(sort_cols) if sort_cols else df
    for column, negative_key, decrease_key in (
        ("volume", "negative_volume_count", "volume_decrease_count"),
        ("total_turnover", "negative_turnover_count", "turnover_decrease_count"),
    ):
        if column not in checked.columns:
            continue
        values = _numeric(checked, column)
        report[negative_key] = int((values < 0).sum())
        if group_cols:
            diffs = values.groupby([checked[col] for col in group_cols]).diff()
        else:
            diffs = values.diff()
        report[decrease_key] = int((diffs < 0).sum())
        if report[negative_key] or report[decrease_key]:
            report["warnings"].append(f"{column}_anomaly")

    return report


def write_health_report(
    input_root: str | Path,
    output_json: str | Path | None = None,
) -> dict[str, Any]:
    report = inspect_raw_health(input_root)
    path = (
        Path(output_json) if output_json else metadata_path(Path(input_root) / "health", "health")
    )
    write_json(path, report)
    report["report_path"] = str(path)
    return report


def format_health_summary(report: dict[str, Any]) -> str:
    return (
        f"status={report['status']} rows={report['row_count']} "
        f"symbols={report['symbol_count']} dates={report['date_count']} "
        f"warnings={len(report['warnings'])} failures={len(report['failures'])}"
    )
