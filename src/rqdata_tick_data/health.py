"""Health checks for raw tick-depth parquet parts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from rqdata_tick_data.storage import load_parquet_parts, metadata_path, write_json

REQUIRED_RAW_COLUMNS = ("order_book_id", "datetime")
SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}
FAIL_ON_SEVERITIES = ("none", "info", "warning", "error")


def _numeric(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def _normalize_fail_on_severity(value: object) -> str:
    text = str(value or "error").strip().lower()
    if not text:
        return "error"
    if text not in FAIL_ON_SEVERITIES:
        raise ValueError("fail_on_severity must be one of: none, info, warning, error.")
    return text


def _append_quality_check(
    checks: list[dict[str, Any]],
    *,
    check: str,
    severity: str,
    message: str,
    **extra: Any,
) -> None:
    checks.append({"check": check, "severity": severity, "message": message, **extra})


def _quality_verdict(
    checks: list[dict[str, Any]],
    *,
    fail_on_severity: str,
) -> dict[str, Any]:
    threshold = _normalize_fail_on_severity(fail_on_severity)
    severity_counts = {
        severity: sum(1 for check in checks if check.get("severity") == severity)
        for severity in ("error", "warning", "info")
    }
    issue_count = int(sum(severity_counts.values()))
    overall = "none"
    for severity in ("error", "warning", "info"):
        if severity_counts[severity]:
            overall = severity
            break
    failing = 0
    if threshold != "none":
        threshold_rank = SEVERITY_RANK[threshold]
        failing = sum(
            1
            for check in checks
            if SEVERITY_RANK.get(str(check.get("severity")), 0) >= threshold_rank
        )
    return {
        "overall_severity": overall,
        "issue_count": issue_count,
        "severity_counts": severity_counts,
        "fail_on_severity": threshold,
        "gate_triggered": bool(failing),
        "gate_status": "fail" if failing else "pass",
        "failing_issue_count": int(failing),
        "sample_failing_checks": [
            str(check.get("check"))
            for check in checks
            if threshold != "none"
            and SEVERITY_RANK.get(str(check.get("severity")), 0) >= SEVERITY_RANK[threshold]
        ][:5],
    }


def _build_quality_checks(report: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    if report["row_count"] == 0:
        _append_quality_check(
            checks,
            check="empty_dataset",
            severity="error",
            message="Raw tick dataset has no rows.",
        )
    if report["missing_required_columns"]:
        _append_quality_check(
            checks,
            check="missing_required_columns",
            severity="error",
            message="Raw tick dataset is missing identity columns.",
            columns=list(report["missing_required_columns"]),
        )
    if int(report.get("timestamp_parse_failure_count") or 0):
        _append_quality_check(
            checks,
            check="timestamp_parse_failures",
            severity="warning",
            message="Some tick timestamps could not be parsed.",
            count=int(report["timestamp_parse_failure_count"]),
        )
    if int(report.get("duplicate_key_count") or 0):
        _append_quality_check(
            checks,
            check="duplicate_symbol_timestamp_rows",
            severity="warning",
            message="Duplicate order_book_id/datetime keys were found.",
            duplicate_keys=int(report["duplicate_key_count"]),
            duplicate_rows=int(report["duplicate_row_count"]),
        )
    if int(report.get("invalid_best_spread_count") or 0):
        _append_quality_check(
            checks,
            check="invalid_best_quote_spread",
            severity="warning",
            message="Best ask is below best bid for some rows.",
            rows=int(report["invalid_best_spread_count"]),
            sample_groups=list(report["invalid_best_spread_groups"]),
        )
    for metric in ("negative_volume_count", "negative_turnover_count"):
        if int(report.get(metric) or 0):
            _append_quality_check(
                checks,
                check=metric,
                severity="warning",
                message=f"{metric} is non-zero.",
                rows=int(report[metric]),
            )
    for metric in ("volume_decrease_count", "turnover_decrease_count"):
        if int(report.get(metric) or 0):
            _append_quality_check(
                checks,
                check=metric,
                severity="warning",
                message=f"{metric} is non-zero for cumulative provider fields.",
                rows=int(report[metric]),
            )
    return checks


def inspect_raw_health(
    input_root: str | Path,
    *,
    fail_on_severity: str = "error",
) -> dict[str, Any]:
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
        "quality_checks": [],
        "quality_verdict": {},
        "status": "pass",
    }

    if df.empty:
        report["failures"].append("empty_dataset")
        report["status"] = "fail"
        report["quality_checks"] = _build_quality_checks(report)
        report["quality_verdict"] = _quality_verdict(
            report["quality_checks"],
            fail_on_severity=fail_on_severity,
        )
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

    report["quality_checks"] = _build_quality_checks(report)
    report["quality_verdict"] = _quality_verdict(
        report["quality_checks"],
        fail_on_severity=fail_on_severity,
    )
    return report


def write_health_report(
    input_root: str | Path,
    output_json: str | Path | None = None,
    *,
    fail_on_severity: str = "error",
) -> dict[str, Any]:
    report = inspect_raw_health(input_root, fail_on_severity=fail_on_severity)
    path = (
        Path(output_json) if output_json else metadata_path(Path(input_root) / "health", "health")
    )
    write_json(path, report)
    report["report_path"] = str(path)
    return report


def format_health_summary(report: dict[str, Any]) -> str:
    verdict = report.get("quality_verdict")
    severity = (
        verdict.get("overall_severity", "unknown")
        if isinstance(verdict, dict)
        else "unknown"
    )
    return (
        f"status={report['status']} rows={report['row_count']} "
        f"symbols={report['symbol_count']} dates={report['date_count']} "
        f"warnings={len(report['warnings'])} failures={len(report['failures'])} "
        f"quality={severity}"
    )
