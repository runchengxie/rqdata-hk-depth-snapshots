"""Tick-vs-daily reconciliation checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from rqdata_tick_data.storage import discover_parquet_parts, load_parquet_parts, write_json
from rqdata_tick_data.symbols import normalize_hk_order_book_id

SEVERITY_RANK = {"info": 0, "warning": 1, "error": 2}
FAIL_ON_SEVERITIES = ("none", "info", "warning", "error")
REFERENCE_POLICIES = ("raw-daily", "cross-clean")
ECONOMIC_MISMATCH_CHECKS = {
    "tick_close_mismatch",
    "tick_volume_mismatch",
    "tick_turnover_mismatch",
}


def _normalize_reference_policy(value: str) -> str:
    policy = value.strip().lower()
    if policy not in REFERENCE_POLICIES:
        raise ValueError("reference_policy must be one of: raw-daily, cross-clean.")
    return policy


def _policy_check_severity(*, check: str, severity: str, reference_policy: str) -> str:
    if reference_policy == "cross-clean" and check in ECONOMIC_MISMATCH_CHECKS:
        return "info"
    return severity


def _reference_policy_metadata(policy: str) -> dict[str, Any]:
    if policy == "cross-clean":
        return {
            "name": policy,
            "gate_reference": "raw-daily",
            "research_reference": "cross-clean",
            "description": (
                "Use cross daily clean assets for research coverage checks. Numeric tick-vs-daily "
                "mismatches are recorded as info because clean/adjusted prices may not share the "
                "raw tick quote basis."
            ),
            "numeric_mismatch_severity": "info",
        }
    return {
        "name": policy,
        "gate_reference": "raw-daily",
        "research_reference": "cross-clean",
        "description": (
            "Use a raw daily reference on the same quote basis as adjust_type=none ticks for "
            "download-quality gates."
        ),
        "numeric_mismatch_severity": "warning",
    }


@dataclass(frozen=True)
class ReconcileConfig:
    price_rtol: float = 1e-4
    price_atol: float = 1e-4
    volume_rtol: float = 1e-4
    volume_atol: float = 1.0
    turnover_rtol: float = 1e-4
    turnover_atol: float = 1.0
    session_start: str = "09:00"
    session_end: str = "16:30"
    sample_limit: int = 20
    fail_on_severity: str = "error"
    reference_policy: str = "raw-daily"

    def to_dict(self) -> dict[str, Any]:
        return {
            "price_rtol": self.price_rtol,
            "price_atol": self.price_atol,
            "volume_rtol": self.volume_rtol,
            "volume_atol": self.volume_atol,
            "turnover_rtol": self.turnover_rtol,
            "turnover_atol": self.turnover_atol,
            "session_start": self.session_start,
            "session_end": self.session_end,
            "sample_limit": self.sample_limit,
            "fail_on_severity": self.fail_on_severity,
            "reference_policy": _normalize_reference_policy(self.reference_policy),
        }


def canonical_daily_symbol(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        normalized = normalize_hk_order_book_id(text)
    except ValueError:
        return text.upper()
    return normalized.removesuffix(".XHKG") + ".HK"


def canonical_tick_symbol(value: object) -> str | None:
    daily = canonical_daily_symbol(value)
    if daily is None:
        return None
    if daily.endswith(".HK") and daily[:5].isdigit():
        return f"{daily[:5]}.XHKG"
    return daily


def _format_date(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    compact = text.replace("-", "")
    if len(compact) >= 8 and compact[:8].isdigit():
        return compact[:8]
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        return None
    return timestamp.strftime("%Y%m%d")


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(float("nan"), index=frame.index, dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _session_time(value: str) -> time:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        return time(parts[0], parts[1])
    if len(parts) == 3:
        return time(parts[0], parts[1], parts[2])
    raise ValueError("Session time must be HH:MM or HH:MM:SS.")


def _quality_verdict(
    checks: list[dict[str, Any]],
    *,
    fail_on_severity: str,
) -> dict[str, Any]:
    threshold = fail_on_severity.strip().lower()
    if threshold not in FAIL_ON_SEVERITIES:
        raise ValueError("fail_on_severity must be one of: none, info, warning, error.")
    severity_counts = {
        severity: sum(1 for check in checks if check.get("severity") == severity)
        for severity in ("error", "warning", "info")
    }
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
        "issue_count": int(sum(severity_counts.values())),
        "severity_counts": severity_counts,
        "fail_on_severity": threshold,
        "gate_triggered": bool(failing),
        "gate_status": "fail" if failing else "pass",
        "failing_issue_count": int(failing),
    }


def _sample(frame: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    return frame.head(limit).where(pd.notna(frame.head(limit)), None).to_dict("records")


def _append_check(
    checks: list[dict[str, Any]],
    *,
    check: str,
    severity: str,
    message: str,
    affected: int,
    samples: pd.DataFrame | None = None,
    sample_limit: int = 20,
    **extra: Any,
) -> None:
    if affected <= 0:
        return
    row = {
        "check": check,
        "severity": severity,
        "message": message,
        "affected_items": int(affected),
        **extra,
    }
    if samples is not None:
        row["sample_rows"] = _sample(samples, sample_limit)
    checks.append(row)


def _read_manifest(path: Path) -> dict[str, Any]:
    manifest_path = path / "manifest.yml"
    if not manifest_path.exists():
        return {}
    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"manifest_path": str(manifest_path), "manifest_error": str(exc)}
    if isinstance(payload, dict):
        return {"manifest_path": str(manifest_path), **payload}
    return {"manifest_path": str(manifest_path)}


def normalize_tick_for_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if work.empty:
        return work
    if "order_book_id" not in work.columns and "symbol" in work.columns:
        work["order_book_id"] = work["symbol"]
    if "order_book_id" not in work.columns:
        work["order_book_id"] = pd.NA
    if "datetime" not in work.columns and "trade_datetime" in work.columns:
        work["datetime"] = work["trade_datetime"]
    if "datetime" in work.columns:
        work["_timestamp"] = pd.to_datetime(work["datetime"], errors="coerce")
    else:
        work["_timestamp"] = pd.Series(pd.NaT, index=work.index)
    if "trading_date" not in work.columns:
        work["trading_date"] = work["_timestamp"].map(_format_date)
    else:
        work["trading_date"] = work["trading_date"].map(_format_date)
    work["symbol_key"] = work["order_book_id"].map(canonical_daily_symbol)
    return work


def _final_cumulative(group: pd.DataFrame, column: str) -> tuple[float | None, bool]:
    values = pd.to_numeric(group[column], errors="coerce") if column in group.columns else None
    if values is None or values.dropna().empty:
        return None, False
    last_raw = values.iloc[-1]
    if pd.notna(last_raw):
        return float(last_raw), False
    fallback = values.max(skipna=True)
    return (float(fallback), True) if pd.notna(fallback) else (None, False)


def aggregate_tick_ohlcv(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = normalize_tick_for_reconciliation(df)
    metadata: dict[str, Any] = {
        "source_rows": int(len(df)),
        "timestamp_parse_failure_count": 0,
        "volume_fallback_count": 0,
        "turnover_fallback_count": 0,
    }
    if work.empty:
        return pd.DataFrame(), metadata
    metadata["timestamp_parse_failure_count"] = int(work["_timestamp"].isna().sum())
    work = work.dropna(subset=["symbol_key", "trading_date"]).copy()
    if work.empty:
        return pd.DataFrame(), metadata

    rows: list[dict[str, Any]] = []
    for (symbol_key, trade_date), group in work.groupby(
        ["symbol_key", "trading_date"],
        sort=True,
        dropna=False,
    ):
        ordered = group.sort_values("_timestamp", na_position="last").copy()
        last = _numeric(ordered, "last")
        valid_last = last.dropna()
        high_source = _numeric(ordered, "high").dropna()
        low_source = _numeric(ordered, "low").dropna()
        if high_source.empty:
            high_source = valid_last
        if low_source.empty:
            low_source = valid_last
        volume, volume_fallback = _final_cumulative(ordered, "volume")
        turnover, turnover_fallback = _final_cumulative(ordered, "total_turnover")
        metadata["volume_fallback_count"] += int(volume_fallback)
        metadata["turnover_fallback_count"] += int(turnover_fallback)
        row = {
            "symbol_key": symbol_key,
            "order_book_id": canonical_tick_symbol(symbol_key),
            "trading_date": trade_date,
            "tick_open": float(valid_last.iloc[0]) if not valid_last.empty else pd.NA,
            "tick_high": float(high_source.max()) if not high_source.empty else pd.NA,
            "tick_low": float(low_source.min()) if not low_source.empty else pd.NA,
            "tick_close": float(valid_last.iloc[-1]) if not valid_last.empty else pd.NA,
            "tick_volume": volume if volume is not None else pd.NA,
            "tick_total_turnover": turnover if turnover is not None else pd.NA,
            "tick_first_timestamp": ordered["_timestamp"].min(),
            "tick_last_timestamp": ordered["_timestamp"].max(),
            "tick_row_count": int(len(ordered)),
            "volume_used_fallback": bool(volume_fallback),
            "turnover_used_fallback": bool(turnover_fallback),
        }
        rows.append(row)
    return pd.DataFrame(rows), metadata


def _normalize_daily_reference(frame: pd.DataFrame, *, source_symbol: str | None) -> pd.DataFrame:
    work = frame.copy()
    if work.empty:
        return work
    date_col = next(
        (column for column in ("trade_date", "trading_date", "date") if column in work.columns),
        None,
    )
    if date_col is None:
        raise ValueError("Daily reference frame is missing trade_date/trading_date/date.")
    if "symbol" not in work.columns:
        work["symbol"] = source_symbol
    if "order_book_id" not in work.columns:
        work["order_book_id"] = work["symbol"].map(canonical_tick_symbol)
    work["trading_date"] = work[date_col].map(_format_date)
    symbol_source = work["symbol"].where(work["symbol"].notna(), work["order_book_id"])
    work["symbol_key"] = symbol_source.map(canonical_daily_symbol)
    columns = [
        "symbol_key",
        "symbol",
        "order_book_id",
        "trading_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "total_turnover",
    ]
    for column in columns:
        if column not in work.columns:
            work[column] = pd.NA
    return work[columns].dropna(subset=["symbol_key", "trading_date"])


def load_daily_reference(
    daily_asset_dir: str | Path,
    *,
    symbol_keys: set[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    root = Path(daily_asset_dir)
    manifest = _read_manifest(root) if root.is_dir() else {}
    if root.is_file():
        frame = _normalize_daily_reference(pd.read_parquet(root), source_symbol=root.stem)
        return frame, {"path": str(root), "manifest": manifest, "files_read": [str(root)]}

    data_root = root / "data" if (root / "data").exists() else root
    parts: list[Path] = []
    if symbol_keys:
        for symbol in sorted(symbol_keys):
            part = data_root / f"{symbol}.parquet"
            if part.exists():
                parts.append(part)
    if not parts:
        parts = discover_parquet_parts(data_root)

    frames = []
    for part in parts:
        source_symbol = part.stem if part.parent == data_root else None
        frames.append(
            _normalize_daily_reference(
                pd.read_parquet(part),
                source_symbol=source_symbol,
            )
        )
    daily = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    metadata = {"path": str(root), "manifest": manifest, "files_read": [str(p) for p in parts]}
    return daily, metadata


def _within_tolerance(
    left: pd.Series,
    right: pd.Series,
    *,
    rtol: float,
    atol: float,
) -> pd.Series:
    delta = (left - right).abs()
    allowed = pd.Series(atol, index=left.index, dtype="float64").where(
        right.abs().isna(),
        right.abs() * rtol + atol,
    )
    return delta <= allowed


def _ohlc_invalid(frame: pd.DataFrame, prefix: str = "") -> pd.Series:
    open_col = f"{prefix}open" if prefix else "open"
    high_col = f"{prefix}high" if prefix else "high"
    low_col = f"{prefix}low" if prefix else "low"
    close_col = f"{prefix}close" if prefix else "close"
    values = {
        column: _numeric(frame, column)
        for column in (open_col, high_col, low_col, close_col)
    }
    high = values[high_col]
    low = values[low_col]
    maximum = pd.concat([values[open_col], low, values[close_col]], axis=1).max(axis=1)
    minimum = pd.concat([values[open_col], high, values[close_col]], axis=1).min(axis=1)
    return (high < maximum) | (low > minimum) | (high < low)


def _quote_ladder_invalid(work: pd.DataFrame) -> pd.Series:
    invalid = pd.Series(False, index=work.index)
    if {"a1", "b1"}.issubset(work.columns):
        a1 = _numeric(work, "a1")
        b1 = _numeric(work, "b1")
        positive = (a1 > 0) & (b1 > 0)
        invalid |= positive & (a1 < b1)
    for level in range(1, 10):
        ask_left, ask_right = f"a{level}", f"a{level + 1}"
        bid_left, bid_right = f"b{level}", f"b{level + 1}"
        if {ask_left, ask_right}.issubset(work.columns):
            left = _numeric(work, ask_left)
            right = _numeric(work, ask_right)
            valid = (left > 0) & (right > 0)
            invalid |= valid & (left > right)
        if {bid_left, bid_right}.issubset(work.columns):
            left = _numeric(work, bid_left)
            right = _numeric(work, bid_right)
            valid = (left > 0) & (right > 0)
            invalid |= valid & (left < right)
    volume_columns = [
        column
        for column in work.columns
        if (column.startswith("a") or column.startswith("b")) and column.endswith("_v")
    ]
    for column in volume_columns:
        invalid |= _numeric(work, column) < 0
    return invalid


def inspect_tick_daily_reconciliation(
    tick_input: str | Path,
    daily_asset_dir: str | Path,
    *,
    config: ReconcileConfig | None = None,
) -> dict[str, Any]:
    cfg = config or ReconcileConfig()
    reference_policy = _normalize_reference_policy(cfg.reference_policy)
    session_start = _session_time(cfg.session_start)
    session_end = _session_time(cfg.session_end)
    raw = load_parquet_parts(tick_input)
    tick_daily, aggregate_meta = aggregate_tick_ohlcv(raw)
    symbol_keys = set(tick_daily.get("symbol_key", pd.Series(dtype="object")).dropna().astype(str))
    daily, reference_meta = load_daily_reference(daily_asset_dir, symbol_keys=symbol_keys)
    checks: list[dict[str, Any]] = []

    if raw.empty:
        _append_check(
            checks,
            check="empty_tick_dataset",
            severity="error",
            message="Raw tick dataset has no rows.",
            affected=1,
            sample_limit=cfg.sample_limit,
        )

    normalized_raw = normalize_tick_for_reconciliation(raw)
    if not normalized_raw.empty:
        parse_failures = int(normalized_raw["_timestamp"].isna().sum())
        _append_check(
            checks,
            check="timestamp_parse_failures",
            severity="warning",
            message="Some tick timestamps could not be parsed.",
            affected=parse_failures,
            samples=normalized_raw.loc[
                normalized_raw["_timestamp"].isna(),
                ["order_book_id", "datetime"],
            ],
            sample_limit=cfg.sample_limit,
        )
        times = normalized_raw["_timestamp"].dt.time
        outlier_mask = normalized_raw["_timestamp"].notna() & (
            (times < session_start) | (times > session_end)
        )
        _append_check(
            checks,
            check="session_time_outlier",
            severity="warning",
            message="Tick timestamps fall outside the accepted HK tick session window.",
            affected=int(outlier_mask.sum()),
            samples=normalized_raw.loc[
                outlier_mask,
                ["order_book_id", "trading_date", "datetime"],
            ],
            sample_limit=cfg.sample_limit,
        )
        quote_invalid = _quote_ladder_invalid(normalized_raw)
        quote_sample_cols = [
            column
            for column in ("order_book_id", "trading_date", "datetime", "a1", "b1", "a2", "b2")
            if column in normalized_raw.columns
        ]
        _append_check(
            checks,
            check="quote_ladder_invalid",
            severity="warning",
            message="Quote depth ladder or quote volume rules were violated.",
            affected=int(quote_invalid.sum()),
            samples=normalized_raw.loc[quote_invalid, quote_sample_cols],
            sample_limit=cfg.sample_limit,
        )

    if not tick_daily.empty:
        tick_invalid = _ohlc_invalid(tick_daily, prefix="tick_")
        _append_check(
            checks,
            check="tick_ohlc_bounds_invalid",
            severity="warning",
            message="Tick-derived OHLC values violate high/low/open/close bounds.",
            affected=int(tick_invalid.sum()),
            samples=tick_daily.loc[tick_invalid],
            sample_limit=cfg.sample_limit,
        )
    if not daily.empty:
        daily_invalid = _ohlc_invalid(daily)
        _append_check(
            checks,
            check="daily_ohlc_bounds_invalid",
            severity="warning",
            message="Daily reference OHLC values violate high/low/open/close bounds.",
            affected=int(daily_invalid.sum()),
            samples=daily.loc[daily_invalid],
            sample_limit=cfg.sample_limit,
        )

    if not tick_daily.empty and not daily.empty:
        date_min = str(tick_daily["trading_date"].min())
        date_max = str(tick_daily["trading_date"].max())
        daily_scoped = daily.loc[
            daily["symbol_key"].isin(symbol_keys)
            & (daily["trading_date"].astype(str) >= date_min)
            & (daily["trading_date"].astype(str) <= date_max)
        ].copy()
        merged = daily_scoped.merge(
            tick_daily,
            on=["symbol_key", "trading_date"],
            how="outer",
            suffixes=("_daily", "_tick"),
            indicator=True,
        )
        daily_active = (_numeric(merged, "volume") > 0) | (_numeric(merged, "total_turnover") > 0)
        missing_tick = (merged["_merge"] == "left_only") & daily_active
        _append_check(
            checks,
            check="daily_active_missing_tick",
            severity="warning",
            message="Daily reference has positive volume or turnover but no matching tick rows.",
            affected=int(missing_tick.sum()),
            samples=merged.loc[
                missing_tick,
                ["symbol_key", "trading_date", "volume", "total_turnover"],
            ],
            sample_limit=cfg.sample_limit,
        )

        matched = merged.loc[merged["_merge"] == "both"].copy()
        if not matched.empty:
            close_ok = _within_tolerance(
                _numeric(matched, "tick_close"),
                _numeric(matched, "close"),
                rtol=cfg.price_rtol,
                atol=cfg.price_atol,
            )
            close_bad = (
                ~close_ok
                & _numeric(matched, "tick_close").notna()
                & _numeric(matched, "close").notna()
            )
            matched["close_delta"] = _numeric(matched, "tick_close") - _numeric(matched, "close")
            _append_check(
                checks,
                check="tick_close_mismatch",
                severity=_policy_check_severity(
                    check="tick_close_mismatch",
                    severity="warning",
                    reference_policy=reference_policy,
                ),
                message="Tick close differs from daily close beyond tolerance.",
                affected=int(close_bad.sum()),
                samples=matched.loc[
                    close_bad,
                    ["symbol_key", "trading_date", "tick_close", "close", "close_delta"],
                ],
                sample_limit=cfg.sample_limit,
            )

            volume_ok = _within_tolerance(
                _numeric(matched, "tick_volume"),
                _numeric(matched, "volume"),
                rtol=cfg.volume_rtol,
                atol=cfg.volume_atol,
            )
            volume_bad = (
                ~volume_ok
                & _numeric(matched, "tick_volume").notna()
                & _numeric(matched, "volume").notna()
            )
            matched["volume_delta"] = _numeric(matched, "tick_volume") - _numeric(matched, "volume")
            _append_check(
                checks,
                check="tick_volume_mismatch",
                severity=_policy_check_severity(
                    check="tick_volume_mismatch",
                    severity="warning",
                    reference_policy=reference_policy,
                ),
                message="Tick cumulative volume differs from daily volume beyond tolerance.",
                affected=int(volume_bad.sum()),
                samples=matched.loc[
                    volume_bad,
                    ["symbol_key", "trading_date", "tick_volume", "volume", "volume_delta"],
                ],
                sample_limit=cfg.sample_limit,
            )

            turnover_ok = _within_tolerance(
                _numeric(matched, "tick_total_turnover"),
                _numeric(matched, "total_turnover"),
                rtol=cfg.turnover_rtol,
                atol=cfg.turnover_atol,
            )
            turnover_bad = (
                ~turnover_ok
                & _numeric(matched, "tick_total_turnover").notna()
                & _numeric(matched, "total_turnover").notna()
            )
            matched["turnover_delta"] = _numeric(matched, "tick_total_turnover") - _numeric(
                matched,
                "total_turnover",
            )
            _append_check(
                checks,
                check="tick_turnover_mismatch",
                severity=_policy_check_severity(
                    check="tick_turnover_mismatch",
                    severity="warning",
                    reference_policy=reference_policy,
                ),
                message=(
                    "Tick cumulative total_turnover differs from daily total_turnover "
                    "beyond tolerance."
                ),
                affected=int(turnover_bad.sum()),
                samples=matched.loc[
                    turnover_bad,
                    [
                        "symbol_key",
                        "trading_date",
                        "tick_total_turnover",
                        "total_turnover",
                        "turnover_delta",
                    ],
                ],
                sample_limit=cfg.sample_limit,
            )

        unmatched_symbols = sorted(symbol_keys - set(daily["symbol_key"].dropna().astype(str)))
    else:
        merged = pd.DataFrame()
        unmatched_symbols = sorted(symbol_keys)

    if unmatched_symbols:
        _append_check(
            checks,
            check="unmatched_daily_reference_symbols",
            severity="warning",
            message="Tick symbols could not be matched in the daily reference asset.",
            affected=len(unmatched_symbols),
            samples=pd.DataFrame({"symbol_key": unmatched_symbols}),
            sample_limit=cfg.sample_limit,
        )

    verdict = _quality_verdict(checks, fail_on_severity=cfg.fail_on_severity)
    summary = {
        "tick_rows": int(len(raw)),
        "tick_symbol_days": int(len(tick_daily)),
        "daily_reference_rows": int(len(daily)),
        "matched_symbol_days": (
            int((merged.get("_merge") == "both").sum()) if not merged.empty else 0
        ),
        "unmatched_symbol_count": len(unmatched_symbols),
        **aggregate_meta,
    }
    return {
        "input_paths": {
            "tick_input": str(tick_input),
            "daily_asset_dir": str(daily_asset_dir),
        },
        "reference_policy": _reference_policy_metadata(reference_policy),
        "tolerance": cfg.to_dict(),
        "reference": reference_meta,
        "summary": summary,
        "quality_checks": checks,
        "quality_verdict": verdict,
        "status": "fail" if verdict["overall_severity"] == "error" else "pass",
    }


def write_reconciliation_report(
    tick_input: str | Path,
    daily_asset_dir: str | Path,
    out: str | Path,
    *,
    config: ReconcileConfig | None = None,
) -> dict[str, Any]:
    report = inspect_tick_daily_reconciliation(tick_input, daily_asset_dir, config=config)
    write_json(out, report)
    report["report_path"] = str(out)
    return report
