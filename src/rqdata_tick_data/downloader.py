"""Probe and download workflows."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd

from rqdata_tick_data.audit import (
    AuditRecord,
    default_audit_path,
    summarize_audit,
    write_audit_records,
)
from rqdata_tick_data.coverage import (
    STATUS_MISSING,
    VALID_STATUS,
    coverage_summary,
    scan_raw_coverage,
)
from rqdata_tick_data.exceptions import DownloadError, ProviderRequestError
from rqdata_tick_data.fields import DEFAULT_TICK_DEPTH_FIELDS
from rqdata_tick_data.rq_client import TickDataProvider
from rqdata_tick_data.runtime import retry_provider_call
from rqdata_tick_data.schema import normalize_tick_frame
from rqdata_tick_data.storage import (
    DEFAULT_PARQUET_COMPRESSION,
    DEFAULT_PARQUET_ENGINE,
    atomic_write_parquet,
    batch_part_path,
    metadata_path,
    symbol_date_part_path,
    validate_parquet_write_options,
    write_json,
)
from rqdata_tick_data.symbols import format_date, iter_dates


@dataclass(frozen=True)
class BatchPlan:
    trade_date: str
    batch_number: int
    symbols: tuple[str, ...]
    part_path: Path


@dataclass(frozen=True)
class UnitPlan:
    trade_date: str
    order_book_id: str
    part_path: Path


@dataclass(frozen=True)
class ProviderBatch:
    trade_date: str
    batch_number: int
    symbols: tuple[str, ...]
    units: tuple[UnitPlan, ...]


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def chunked(items: Sequence[str], size: int) -> list[tuple[str, ...]]:
    if size < 1:
        raise ValueError("batch_size must be at least 1.")
    return [tuple(items[i : i + size]) for i in range(0, len(items), size)]


def build_batch_plan(
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    output_root: str | Path,
    batch_size: int,
    trade_dates: Sequence[str] | None = None,
) -> list[BatchPlan]:
    root = Path(output_root)
    batches: list[BatchPlan] = []
    dates = list(trade_dates) if trade_dates is not None else list(iter_dates(start_date, end_date))
    for trade_date in dates:
        for batch_number, symbol_batch in enumerate(chunked(list(symbols), batch_size)):
            batches.append(
                BatchPlan(
                    trade_date=trade_date,
                    batch_number=batch_number,
                    symbols=symbol_batch,
                    part_path=batch_part_path(root, trade_date, batch_number),
                )
            )
    return batches


def build_symbol_date_plan(
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    output_root: str | Path,
    trade_dates: Sequence[str] | None = None,
) -> list[UnitPlan]:
    root = Path(output_root)
    units: list[UnitPlan] = []
    dates = list(trade_dates) if trade_dates is not None else list(iter_dates(start_date, end_date))
    for trade_date in dates:
        for symbol in symbols:
            units.append(
                UnitPlan(
                    trade_date=trade_date,
                    order_book_id=symbol,
                    part_path=symbol_date_part_path(root, trade_date, symbol),
                )
            )
    return units


def normalize_raw_layout(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"symbol-date", "symbol", "symbol-date-v1"}:
        return "symbol-date"
    if normalized in {"batch", "legacy-batch", "legacy"}:
        return "batch"
    raise ValueError("raw_layout must be one of: symbol-date, batch.")


def normalize_calendar(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"provider", "rqdata", "trading", "trading-days"}:
        return "provider"
    if normalized in {"calendar", "natural", "all-days"}:
        return "calendar"
    raise ValueError("calendar must be one of: provider, calendar.")


def _resolve_trade_dates(
    *,
    provider: TickDataProvider | None,
    start_date: str,
    end_date: str,
    calendar: str,
) -> tuple[list[str], str]:
    normalized = normalize_calendar(calendar)
    if normalized == "provider" and provider is not None and hasattr(provider, "get_trading_dates"):
        dates = [format_date(value) for value in provider.get_trading_dates(start_date, end_date)]
        return dates, "provider"
    source = "calendar"
    if normalized == "provider" and provider is None:
        source = "calendar_fallback_no_provider"
    elif normalized == "provider":
        source = "calendar_fallback_no_provider_method"
    return list(iter_dates(start_date, end_date)), source


def _quota_snapshot(provider: TickDataProvider | None) -> dict[str, Any]:
    if provider is None or not hasattr(provider, "quota_snapshot"):
        return {"available": False}
    try:
        snapshot = provider.quota_snapshot()
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    if snapshot is None:
        return {"available": False}
    return {"available": True, "value": snapshot}


def _quota_payload(snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
    if not snapshot or not snapshot.get("available"):
        return None
    value = snapshot.get("value")
    return value if isinstance(value, dict) else None


def _quota_int(payload: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None


def _quota_used_limit(snapshot: dict[str, Any] | None) -> tuple[int, int] | None:
    payload = _quota_payload(snapshot)
    if payload is None:
        return None
    used = _quota_int(payload, "bytes_used", "used_bytes", "traffic_used", "used")
    limit = _quota_int(payload, "bytes_limit", "limit_bytes", "traffic_limit", "limit")
    if used is None or limit is None or limit <= 0:
        return None
    return used, limit


def _quota_used(snapshot: dict[str, Any] | None) -> int | None:
    values = _quota_used_limit(snapshot)
    return values[0] if values else None


def _quota_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> int | None:
    before_used = _quota_used(before)
    after_used = _quota_used(after)
    if before_used is None or after_used is None:
        return None
    return max(0, after_used - before_used)


def _estimate_next_quota_delta(
    successful_deltas: Sequence[int],
    *,
    safety_multiplier: float,
) -> int | None:
    deltas = [int(value) for value in successful_deltas if int(value) > 0]
    if not deltas:
        return None
    series = pd.Series(deltas, dtype="float64")
    estimate = max(float(series.quantile(0.90)), float(deltas[-1])) * safety_multiplier
    return int(estimate)


def _quota_guard_decision(
    snapshot: dict[str, Any],
    successful_deltas: Sequence[int],
    *,
    enabled: bool,
    stop_ratio: float,
    safety_multiplier: float,
) -> dict[str, Any]:
    values = _quota_used_limit(snapshot)
    if not enabled or values is None:
        return {
            "available": values is not None,
            "blocked": False,
            "estimated_next_delta_bytes": None,
        }
    used, limit = values
    estimate = _estimate_next_quota_delta(
        successful_deltas,
        safety_multiplier=safety_multiplier,
    )
    if estimate is None:
        return {
            "available": True,
            "blocked": False,
            "bytes_used": used,
            "bytes_limit": limit,
            "estimated_next_delta_bytes": None,
        }
    threshold = int(limit * stop_ratio)
    blocked = used + estimate >= threshold
    return {
        "available": True,
        "blocked": blocked,
        "bytes_used": used,
        "bytes_limit": limit,
        "stop_threshold_bytes": threshold,
        "estimated_next_delta_bytes": estimate,
    }


def _audit_record(
    *,
    run_id: str,
    chunk_id: str,
    unit: UnitPlan,
    status: str,
    rows: int | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    duration_seconds: float | None = None,
    quota_before: dict[str, Any] | None = None,
    quota_after: dict[str, Any] | None = None,
    quota_delta: int | None = None,
    attempts: int | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> AuditRecord:
    return AuditRecord(
        run_id=run_id,
        chunk_id=chunk_id,
        trade_date=unit.trade_date,
        order_book_id=unit.order_book_id,
        status=status,
        part_path=str(unit.part_path),
        rows=rows,
        started_at=started_at,
        finished_at=finished_at,
        duration_seconds=duration_seconds,
        quota_before_bytes_used=_quota_used(quota_before),
        quota_after_bytes_used=_quota_used(quota_after),
        quota_delta_bytes=quota_delta,
        attempts=attempts,
        error_type=error_type,
        error_message=error_message,
    )


def _storage_settings(
    *,
    raw_layout: str,
    parquet_engine: str,
    parquet_compression: str | None,
    parquet_compression_level: int | None,
) -> dict[str, Any]:
    writer = validate_parquet_write_options(
        engine=parquet_engine,
        compression=parquet_compression,
        compression_level=parquet_compression_level,
    )
    return {
        "raw_layout": raw_layout,
        "layout_version": "symbol_date.v1" if raw_layout == "symbol-date" else "legacy_batch.v1",
        "parquet": writer,
    }


def _base_metadata(
    *,
    kind: str,
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    fields: Sequence[str],
    output_root: str | Path,
    batch_size: int,
    storage: dict[str, Any],
    trade_dates: Sequence[str],
    calendar_source: str,
    adjust_type: str,
    time_slice: str | None,
) -> dict[str, Any]:
    return {
        "run_id": uuid.uuid4().hex,
        "kind": kind,
        "provider": "rqdata",
        "market": "hk",
        "frequency": "tick",
        "start_date": format_date(start_date),
        "end_date": format_date(end_date),
        "symbols_requested": list(symbols),
        "fields_requested": list(fields),
        "batch_size": batch_size,
        "trade_dates": list(trade_dates),
        "trade_date_count": len(trade_dates),
        "calendar_source": calendar_source,
        "adjust_type": adjust_type,
        "time_slice": time_slice,
        "output_root": str(output_root),
        "storage": storage,
        "raw_layout": storage["raw_layout"],
        "layout_version": storage["layout_version"],
        "parquet": storage["parquet"],
        "created_at": utc_now_iso(),
        "completed_batches": [],
        "skipped_batches": [],
        "failed_batches": [],
        "planned_units": [],
        "completed_units": [],
        "skipped_units": [],
        "invalid_units": [],
        "empty_units": [],
        "failed_units": [],
        "quota_blocked_batches": [],
        "quota_blocked_units": [],
        "audit_path": None,
        "audit_status_counts": {},
        "quota_guard": {},
        "rows": 0,
    }


def _unit_info(unit: UnitPlan, **extra: Any) -> dict[str, Any]:
    return {
        "trade_date": unit.trade_date,
        "order_book_id": unit.order_book_id,
        "part_path": str(unit.part_path),
        **extra,
    }


def _provider_batches(units: Sequence[UnitPlan], batch_size: int) -> list[ProviderBatch]:
    by_date: dict[str, list[UnitPlan]] = {}
    for unit in units:
        by_date.setdefault(unit.trade_date, []).append(unit)

    batches: list[ProviderBatch] = []
    for trade_date in sorted(by_date):
        for batch_number, unit_batch in enumerate(chunked(by_date[trade_date], batch_size)):
            batches.append(
                ProviderBatch(
                    trade_date=trade_date,
                    batch_number=batch_number,
                    symbols=tuple(unit.order_book_id for unit in unit_batch),
                    units=tuple(unit_batch),
                )
            )
    return batches


def _provider_batch_info(batch: ProviderBatch, **extra: Any) -> dict[str, Any]:
    return {
        "trade_date": batch.trade_date,
        "batch_number": batch.batch_number,
        "symbols": list(batch.symbols),
        "units": [_unit_info(unit) for unit in batch.units],
        **extra,
    }


def _coverage_by_unit(
    rows: Sequence[dict[str, Any]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    indexed: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        trade_date = row.get("trading_date")
        symbol = row.get("order_book_id")
        if trade_date and symbol:
            indexed.setdefault((str(trade_date), str(symbol)), []).append(row)
    return indexed


def _valid_coverage_for_unit(
    rows_by_unit: dict[tuple[str, str], list[dict[str, Any]]],
    unit: UnitPlan,
) -> dict[str, Any] | None:
    for row in rows_by_unit.get((unit.trade_date, unit.order_book_id), []):
        if row.get("status") == VALID_STATUS:
            return row
    return None


def _invalid_coverage_for_unit(
    rows_by_unit: dict[tuple[str, str], list[dict[str, Any]]],
    unit: UnitPlan,
    coverage_rows: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    for row in rows_by_unit.get((unit.trade_date, unit.order_book_id), []):
        if row.get("status") != VALID_STATUS:
            return row
    unit_path = str(unit.part_path)
    for row in coverage_rows:
        if row.get("file_path") == unit_path and row.get("status") != VALID_STATUS:
            return row
    return None


def _filter_unit_frame(normalized: pd.DataFrame, unit: UnitPlan) -> pd.DataFrame:
    if normalized.empty or not {"order_book_id", "trading_date"}.issubset(normalized.columns):
        return normalized.iloc[0:0].copy()
    symbol_values = normalized["order_book_id"].astype("string")
    date_values = normalized["trading_date"].astype("string")
    mask = (symbol_values == unit.order_book_id) & (date_values == unit.trade_date)
    return normalized.loc[mask].copy()


def _download_symbol_date_tick_depth(
    *,
    provider: TickDataProvider | None,
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    output_root: str | Path,
    fields: Sequence[str],
    batch_size: int,
    resume: bool,
    continue_on_error: bool,
    dry_run: bool,
    metadata_kind: str,
    storage: dict[str, Any],
    trade_dates: Sequence[str],
    calendar_source: str,
    adjust_type: str,
    time_slice: str | None,
    retry_max_attempts: int,
    retry_backoff_seconds: float,
    retry_max_backoff_seconds: float,
    quota_guard_enabled: bool,
    quota_stop_ratio: float,
    quota_safety_multiplier: float,
    audit_output: str | Path | None,
) -> dict[str, Any]:
    root = Path(output_root)
    units = build_symbol_date_plan(symbols, start_date, end_date, root, trade_dates=trade_dates)
    metadata = _base_metadata(
        kind=metadata_kind,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        output_root=root,
        batch_size=batch_size,
        storage=storage,
        trade_dates=trade_dates,
        calendar_source=calendar_source,
        adjust_type=adjust_type,
        time_slice=time_slice,
    )
    run_id = str(metadata["run_id"])
    audit_records: list[AuditRecord] = []
    audit_file = Path(audit_output) if audit_output else default_audit_path(root, metadata_kind)
    metadata["audit_path"] = str(audit_file)
    metadata["quota_guard"] = {
        "enabled": quota_guard_enabled,
        "stop_ratio": quota_stop_ratio,
        "safety_multiplier": quota_safety_multiplier,
        "available": False,
    }
    metadata["planned_units"] = [_unit_info(unit) for unit in units]

    coverage_rows = scan_raw_coverage(root, requested_fields=fields) if resume else []
    rows_by_unit = _coverage_by_unit(coverage_rows)
    metadata["coverage"] = coverage_summary(coverage_rows)

    units_to_download: list[UnitPlan] = []
    for unit in units:
        if resume:
            valid = _valid_coverage_for_unit(rows_by_unit, unit)
            if valid is not None:
                metadata["skipped_units"].append(
                    _unit_info(
                        unit,
                        validation_status=VALID_STATUS,
                        existing_file_path=valid.get("file_path"),
                        row_count=valid.get("row_count", 0),
                    )
                )
                audit_records.append(
                    _audit_record(
                        run_id=run_id,
                        chunk_id=f"{unit.trade_date}:resume",
                        unit=unit,
                        status="skipped_existing",
                        rows=int(valid.get("row_count") or 0),
                        attempts=0,
                    )
                )
                continue
            invalid = _invalid_coverage_for_unit(rows_by_unit, unit, coverage_rows)
            if invalid is not None:
                metadata["invalid_units"].append(
                    _unit_info(
                        unit,
                        validation_status=invalid.get("status"),
                        existing_file_path=invalid.get("file_path"),
                        reason=invalid.get("reason"),
                    )
                )
            else:
                metadata["invalid_units"].append(
                    _unit_info(unit, validation_status=STATUS_MISSING, reason="missing local part")
                )
        units_to_download.append(unit)

    metadata["skipped_batches"] = [
        _provider_batch_info(batch, validation_status=VALID_STATUS)
        for batch in _provider_batches(
            [
                UnitPlan(
                    trade_date=str(unit["trade_date"]),
                    order_book_id=str(unit["order_book_id"]),
                    part_path=Path(str(unit["part_path"])),
                )
                for unit in metadata["skipped_units"]
            ],
            batch_size,
        )
    ]
    provider_batches = _provider_batches(units_to_download, batch_size)
    metadata["planned_batches"] = [_provider_batch_info(batch) for batch in provider_batches]
    metadata["dry_run"] = dry_run

    if dry_run:
        metadata["audit_status_counts"] = summarize_audit(audit_records)
        return metadata
    if provider is None:
        raise DownloadError("A provider is required unless dry_run=True.")

    metadata["quota_before"] = _quota_snapshot(provider)
    metadata_file = metadata_path(root, metadata_kind)
    writer = storage["parquet"]
    successful_quota_deltas: list[int] = []

    try:
        for batch in provider_batches:
            batch_info = _provider_batch_info(batch)
            chunk_id = f"{batch.trade_date}:{batch.batch_number:04d}"
            quota_before = _quota_snapshot(provider)
            guard = _quota_guard_decision(
                quota_before,
                successful_quota_deltas,
                enabled=quota_guard_enabled,
                stop_ratio=quota_stop_ratio,
                safety_multiplier=quota_safety_multiplier,
            )
            metadata["quota_guard"]["available"] = bool(
                metadata["quota_guard"].get("available") or guard.get("available")
            )
            batch_info["quota_before"] = quota_before
            batch_info["quota_guard"] = guard
            if guard["blocked"]:
                batch_info["category"] = "quota_guard"
                batch_info["error"] = "quota guard blocked provider request"
                metadata["quota_blocked_batches"].append(batch_info)
                for unit in batch.units:
                    info = _unit_info(
                        unit,
                        category="quota_guard",
                        estimated_next_delta_bytes=guard.get("estimated_next_delta_bytes"),
                    )
                    metadata["quota_blocked_units"].append(info)
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status="quota_blocked",
                            quota_before=quota_before,
                            error_type="quota_guard",
                            error_message="quota guard blocked provider request",
                        )
                    )
                continue

            started_at = utc_now_iso()
            started_clock = perf_counter()
            try:
                batch_symbols = batch.symbols
                batch_trade_date = batch.trade_date

                def fetch_batch(
                    symbols: Sequence[str] = batch_symbols,
                    trade_date: str = batch_trade_date,
                ) -> pd.DataFrame:
                    return provider.get_price(
                        order_book_ids=symbols,
                        start_date=trade_date,
                        end_date=trade_date,
                        fields=fields,
                        adjust_type=adjust_type,
                        time_slice=time_slice,
                    )

                result = retry_provider_call(
                    "get_price",
                    fetch_batch,
                    max_attempts=retry_max_attempts,
                    backoff_seconds=retry_backoff_seconds,
                    max_backoff_seconds=retry_max_backoff_seconds,
                )
                raw = result.value
                quota_after = _quota_snapshot(provider)
                quota_delta = _quota_delta(quota_before, quota_after)
                if quota_delta:
                    successful_quota_deltas.append(quota_delta)
                normalized = normalize_tick_frame(raw, fields)
                batch_rows = 0
                batch_columns = list(normalized.columns)
                finished_at = utc_now_iso()
                duration_seconds = round(perf_counter() - started_clock, 6)
                for unit in batch.units:
                    unit_frame = _filter_unit_frame(normalized, unit)
                    atomic_write_parquet(unit_frame, unit.part_path, **writer)
                    row_count = int(len(unit_frame))
                    batch_rows += row_count
                    status = "written"
                    if row_count == 0:
                        status = "empty_remote"
                        metadata["empty_units"].append(
                            _unit_info(unit, reason="provider returned no rows")
                        )
                    metadata["completed_units"].append(
                        _unit_info(
                            unit,
                            rows=row_count,
                            columns=list(unit_frame.columns),
                            attempts=result.attempts,
                            quota_delta_bytes=quota_delta,
                        )
                    )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status=status,
                            rows=row_count,
                            started_at=started_at,
                            finished_at=finished_at,
                            duration_seconds=duration_seconds,
                            quota_before=quota_before,
                            quota_after=quota_after,
                            quota_delta=quota_delta,
                            attempts=result.attempts,
                        )
                    )
                batch_info["rows"] = batch_rows
                batch_info["columns"] = batch_columns
                batch_info["attempts"] = result.attempts
                batch_info["quota_after"] = quota_after
                batch_info["quota_delta_bytes"] = quota_delta
                metadata["rows"] += batch_rows
                metadata["completed_batches"].append(batch_info)
            except Exception as exc:
                category = getattr(exc, "category", "download_error")
                quota_after = _quota_snapshot(provider)
                quota_delta = _quota_delta(quota_before, quota_after)
                failed_batch = {
                    **batch_info,
                    "category": category,
                    "error": str(exc),
                    "quota_after": quota_after,
                    "quota_delta_bytes": quota_delta,
                }
                metadata["failed_batches"].append(failed_batch)
                for unit in batch.units:
                    if category == "quota":
                        metadata["quota_blocked_units"].append(
                            _unit_info(unit, category=category, error=str(exc))
                        )
                    else:
                        metadata["failed_units"].append(
                            _unit_info(unit, category=category, error=str(exc))
                        )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status="quota_blocked" if category == "quota" else "failed",
                            started_at=started_at,
                            finished_at=utc_now_iso(),
                            duration_seconds=round(perf_counter() - started_clock, 6),
                            quota_before=quota_before,
                            quota_after=quota_after,
                            quota_delta=quota_delta,
                            error_type=str(category),
                            error_message=str(exc),
                        )
                    )
                if category == "quota" or not continue_on_error:
                    raise
    finally:
        metadata["quota_after"] = _quota_snapshot(provider)
        metadata["audit_status_counts"] = summarize_audit(audit_records)
        if audit_records:
            write_audit_records(audit_file, audit_records)
        write_json(metadata_file, metadata)
        metadata["metadata_path"] = str(metadata_file)

    if metadata["failed_batches"] and not continue_on_error:
        raise DownloadError("Download failed before completion.")
    return metadata


def _batch_part_valid(
    part_path: Path,
    *,
    trade_date: str,
    symbols: Sequence[str],
    fields: Sequence[str],
) -> tuple[bool, list[dict[str, Any]]]:
    if not part_path.exists():
        return False, [
            {
                "status": STATUS_MISSING,
                "file_path": str(part_path),
                "reason": "missing local part",
            }
        ]
    rows = scan_raw_coverage(part_path, requested_fields=fields)
    valid_symbols = {
        str(row["order_book_id"])
        for row in rows
        if row.get("status") == VALID_STATUS and row.get("trading_date") == trade_date
    }
    return set(symbols).issubset(valid_symbols), rows


def _download_batch_tick_depth(
    *,
    provider: TickDataProvider | None,
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    output_root: str | Path,
    fields: Sequence[str],
    batch_size: int,
    resume: bool,
    continue_on_error: bool,
    dry_run: bool,
    metadata_kind: str,
    storage: dict[str, Any],
    trade_dates: Sequence[str],
    calendar_source: str,
    adjust_type: str,
    time_slice: str | None,
    retry_max_attempts: int,
    retry_backoff_seconds: float,
    retry_max_backoff_seconds: float,
    quota_guard_enabled: bool,
    quota_stop_ratio: float,
    quota_safety_multiplier: float,
    audit_output: str | Path | None,
) -> dict[str, Any]:
    root = Path(output_root)
    plans = build_batch_plan(
        symbols,
        start_date,
        end_date,
        root,
        batch_size,
        trade_dates=trade_dates,
    )
    metadata = _base_metadata(
        kind=metadata_kind,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        output_root=root,
        batch_size=batch_size,
        storage=storage,
        trade_dates=trade_dates,
        calendar_source=calendar_source,
        adjust_type=adjust_type,
        time_slice=time_slice,
    )
    run_id = str(metadata["run_id"])
    audit_records: list[AuditRecord] = []
    audit_file = Path(audit_output) if audit_output else default_audit_path(root, metadata_kind)
    metadata["audit_path"] = str(audit_file)
    metadata["quota_guard"] = {
        "enabled": quota_guard_enabled,
        "stop_ratio": quota_stop_ratio,
        "safety_multiplier": quota_safety_multiplier,
        "available": False,
    }
    metadata["planned_units"] = [
        {
            "trade_date": plan.trade_date,
            "order_book_id": symbol,
            "part_path": str(plan.part_path),
        }
        for plan in plans
        for symbol in plan.symbols
    ]
    metadata["planned_batches"] = [
        {
            "trade_date": plan.trade_date,
            "batch_number": plan.batch_number,
            "symbols": list(plan.symbols),
            "part_path": str(plan.part_path),
        }
        for plan in plans
    ]
    metadata["coverage"] = coverage_summary(scan_raw_coverage(root, requested_fields=fields))
    metadata["dry_run"] = dry_run

    plans_to_download: list[BatchPlan] = []
    for plan in plans:
        batch_info = {
            "trade_date": plan.trade_date,
            "batch_number": plan.batch_number,
            "symbols": list(plan.symbols),
            "part_path": str(plan.part_path),
        }
        if resume:
            is_valid, rows = _batch_part_valid(
                plan.part_path,
                trade_date=plan.trade_date,
                symbols=plan.symbols,
                fields=fields,
            )
            if is_valid:
                metadata["skipped_batches"].append(
                    {**batch_info, "validation_status": VALID_STATUS}
                )
                for symbol in plan.symbols:
                    row = next(
                        (
                            item
                            for item in rows
                            if item.get("status") == VALID_STATUS
                            and item.get("trading_date") == plan.trade_date
                            and item.get("order_book_id") == symbol
                        ),
                        {},
                    )
                    metadata["skipped_units"].append(
                        {
                            "trade_date": plan.trade_date,
                            "order_book_id": symbol,
                            "part_path": str(plan.part_path),
                            "validation_status": VALID_STATUS,
                            "existing_file_path": row.get("file_path", str(plan.part_path)),
                            "row_count": row.get("row_count", 0),
                        }
                    )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=f"{plan.trade_date}:{plan.batch_number:04d}:resume",
                            unit=UnitPlan(plan.trade_date, symbol, plan.part_path),
                            status="skipped_existing",
                            rows=int(row.get("row_count") or 0),
                            attempts=0,
                        )
                    )
                continue
            for symbol in plan.symbols:
                invalid_row = next(
                    (
                        item
                        for item in rows
                        if item.get("order_book_id") in {symbol, None}
                        or item.get("file_path") == str(plan.part_path)
                    ),
                    {"status": STATUS_MISSING, "reason": "missing local part"},
                )
                metadata["invalid_units"].append(
                    {
                        "trade_date": plan.trade_date,
                        "order_book_id": symbol,
                        "part_path": str(plan.part_path),
                        "validation_status": invalid_row.get("status"),
                        "existing_file_path": invalid_row.get("file_path"),
                        "reason": invalid_row.get("reason"),
                    }
                )
        plans_to_download.append(plan)

    if dry_run:
        metadata["planned_batches"] = [
            {
                "trade_date": plan.trade_date,
                "batch_number": plan.batch_number,
                "symbols": list(plan.symbols),
                "part_path": str(plan.part_path),
            }
            for plan in plans_to_download
        ]
        metadata["audit_status_counts"] = summarize_audit(audit_records)
        return metadata
    if provider is None:
        raise DownloadError("A provider is required unless dry_run=True.")

    metadata["quota_before"] = _quota_snapshot(provider)
    metadata_file = metadata_path(root, metadata_kind)
    writer = storage["parquet"]
    successful_quota_deltas: list[int] = []

    try:
        for plan in plans_to_download:
            batch_info = {
                "trade_date": plan.trade_date,
                "batch_number": plan.batch_number,
                "symbols": list(plan.symbols),
                "part_path": str(plan.part_path),
            }
            chunk_id = f"{plan.trade_date}:{plan.batch_number:04d}"
            quota_before = _quota_snapshot(provider)
            guard = _quota_guard_decision(
                quota_before,
                successful_quota_deltas,
                enabled=quota_guard_enabled,
                stop_ratio=quota_stop_ratio,
                safety_multiplier=quota_safety_multiplier,
            )
            metadata["quota_guard"]["available"] = bool(
                metadata["quota_guard"].get("available") or guard.get("available")
            )
            batch_info["quota_before"] = quota_before
            batch_info["quota_guard"] = guard
            if guard["blocked"]:
                batch_info["category"] = "quota_guard"
                batch_info["error"] = "quota guard blocked provider request"
                metadata["quota_blocked_batches"].append(batch_info)
                for symbol in plan.symbols:
                    unit = UnitPlan(plan.trade_date, symbol, plan.part_path)
                    metadata["quota_blocked_units"].append(
                        _unit_info(
                            unit,
                            category="quota_guard",
                            estimated_next_delta_bytes=guard.get("estimated_next_delta_bytes"),
                        )
                    )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status="quota_blocked",
                            quota_before=quota_before,
                            error_type="quota_guard",
                            error_message="quota guard blocked provider request",
                        )
                    )
                continue

            started_at = utc_now_iso()
            started_clock = perf_counter()
            try:
                plan_symbols = plan.symbols
                plan_trade_date = plan.trade_date

                def fetch_plan(
                    symbols: Sequence[str] = plan_symbols,
                    trade_date: str = plan_trade_date,
                ) -> pd.DataFrame:
                    return provider.get_price(
                        order_book_ids=symbols,
                        start_date=trade_date,
                        end_date=trade_date,
                        fields=fields,
                        adjust_type=adjust_type,
                        time_slice=time_slice,
                    )

                result = retry_provider_call(
                    "get_price",
                    fetch_plan,
                    max_attempts=retry_max_attempts,
                    backoff_seconds=retry_backoff_seconds,
                    max_backoff_seconds=retry_max_backoff_seconds,
                )
                raw = result.value
                quota_after = _quota_snapshot(provider)
                quota_delta = _quota_delta(quota_before, quota_after)
                if quota_delta:
                    successful_quota_deltas.append(quota_delta)
                normalized = normalize_tick_frame(raw, fields)
                atomic_write_parquet(normalized, plan.part_path, **writer)
                finished_at = utc_now_iso()
                duration_seconds = round(perf_counter() - started_clock, 6)
                batch_info["rows"] = int(len(normalized))
                batch_info["columns"] = list(normalized.columns)
                batch_info["attempts"] = result.attempts
                batch_info["quota_after"] = quota_after
                batch_info["quota_delta_bytes"] = quota_delta
                metadata["rows"] += int(len(normalized))
                metadata["completed_batches"].append(batch_info)
                for symbol in plan.symbols:
                    unit = UnitPlan(plan.trade_date, symbol, plan.part_path)
                    unit_frame = _filter_unit_frame(
                        normalized,
                        unit,
                    )
                    unit_rows = int(len(unit_frame))
                    status = "written"
                    if unit_rows == 0:
                        status = "empty_remote"
                        metadata["empty_units"].append(
                            {
                                "trade_date": plan.trade_date,
                                "order_book_id": symbol,
                                "part_path": str(plan.part_path),
                                "reason": "provider returned no rows",
                            }
                        )
                    metadata["completed_units"].append(
                        {
                            "trade_date": plan.trade_date,
                            "order_book_id": symbol,
                            "part_path": str(plan.part_path),
                            "rows": unit_rows,
                            "columns": list(unit_frame.columns),
                            "attempts": result.attempts,
                            "quota_delta_bytes": quota_delta,
                        }
                    )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status=status,
                            rows=unit_rows,
                            started_at=started_at,
                            finished_at=finished_at,
                            duration_seconds=duration_seconds,
                            quota_before=quota_before,
                            quota_after=quota_after,
                            quota_delta=quota_delta,
                            attempts=result.attempts,
                        )
                    )
            except Exception as exc:
                category = getattr(exc, "category", "download_error")
                quota_after = _quota_snapshot(provider)
                quota_delta = _quota_delta(quota_before, quota_after)
                failed_info = {
                    **batch_info,
                    "category": category,
                    "error": str(exc),
                    "quota_after": quota_after,
                    "quota_delta_bytes": quota_delta,
                }
                metadata["failed_batches"].append(failed_info)
                for symbol in plan.symbols:
                    unit = UnitPlan(plan.trade_date, symbol, plan.part_path)
                    if category == "quota":
                        metadata["quota_blocked_units"].append(
                            _unit_info(unit, category=category, error=str(exc))
                        )
                    else:
                        metadata["failed_units"].append(
                            _unit_info(unit, category=category, error=str(exc))
                        )
                    audit_records.append(
                        _audit_record(
                            run_id=run_id,
                            chunk_id=chunk_id,
                            unit=unit,
                            status="quota_blocked" if category == "quota" else "failed",
                            started_at=started_at,
                            finished_at=utc_now_iso(),
                            duration_seconds=round(perf_counter() - started_clock, 6),
                            quota_before=quota_before,
                            quota_after=quota_after,
                            quota_delta=quota_delta,
                            error_type=str(category),
                            error_message=str(exc),
                        )
                    )
                if category == "quota" or not continue_on_error:
                    raise
    finally:
        metadata["quota_after"] = _quota_snapshot(provider)
        metadata["audit_status_counts"] = summarize_audit(audit_records)
        if audit_records:
            write_audit_records(audit_file, audit_records)
        write_json(metadata_file, metadata)
        metadata["metadata_path"] = str(metadata_file)

    if metadata["failed_batches"] and not continue_on_error:
        raise DownloadError("Download failed before completion.")
    return metadata


def download_tick_depth(
    *,
    provider: TickDataProvider | None,
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    output_root: str | Path,
    fields: Sequence[str] | None = None,
    batch_size: int = 5,
    resume: bool = True,
    continue_on_error: bool = False,
    dry_run: bool = False,
    metadata_kind: str = "download",
    raw_layout: str = "symbol-date",
    calendar: str = "provider",
    adjust_type: str = "none",
    time_slice: str | None = None,
    parquet_engine: str = DEFAULT_PARQUET_ENGINE,
    parquet_compression: str | None = DEFAULT_PARQUET_COMPRESSION,
    parquet_compression_level: int | None = None,
    retry_max_attempts: int = 1,
    retry_backoff_seconds: float = 0.0,
    retry_max_backoff_seconds: float = 60.0,
    quota_guard: bool = True,
    quota_stop_ratio: float = 0.95,
    quota_safety_multiplier: float = 1.2,
    audit_output: str | Path | None = None,
) -> dict[str, Any]:
    """Download tick-depth snapshots into parquet parts and write run metadata."""
    selected_fields = list(fields or DEFAULT_TICK_DEPTH_FIELDS)
    if quota_stop_ratio <= 0 or quota_stop_ratio > 1:
        raise ValueError("quota_stop_ratio must be in (0, 1].")
    if quota_safety_multiplier <= 0:
        raise ValueError("quota_safety_multiplier must be positive.")
    layout = normalize_raw_layout(raw_layout)
    normalized_calendar = normalize_calendar(calendar)
    trade_dates, calendar_source = _resolve_trade_dates(
        provider=provider,
        start_date=start_date,
        end_date=end_date,
        calendar=normalized_calendar,
    )
    storage = _storage_settings(
        raw_layout=layout,
        parquet_engine=parquet_engine,
        parquet_compression=parquet_compression,
        parquet_compression_level=parquet_compression_level,
    )
    if layout == "batch":
        return _download_batch_tick_depth(
            provider=provider,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            output_root=output_root,
            fields=selected_fields,
            batch_size=batch_size,
            resume=resume,
            continue_on_error=continue_on_error,
            dry_run=dry_run,
            metadata_kind=metadata_kind,
            storage=storage,
            trade_dates=trade_dates,
            calendar_source=calendar_source,
            adjust_type=adjust_type,
            time_slice=time_slice,
            retry_max_attempts=retry_max_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            retry_max_backoff_seconds=retry_max_backoff_seconds,
            quota_guard_enabled=quota_guard,
            quota_stop_ratio=quota_stop_ratio,
            quota_safety_multiplier=quota_safety_multiplier,
            audit_output=audit_output,
        )
    return _download_symbol_date_tick_depth(
        provider=provider,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        output_root=output_root,
        fields=selected_fields,
        batch_size=batch_size,
        resume=resume,
        continue_on_error=continue_on_error,
        dry_run=dry_run,
        metadata_kind=metadata_kind,
        storage=storage,
        trade_dates=trade_dates,
        calendar_source=calendar_source,
        adjust_type=adjust_type,
        time_slice=time_slice,
        retry_max_attempts=retry_max_attempts,
        retry_backoff_seconds=retry_backoff_seconds,
        retry_max_backoff_seconds=retry_max_backoff_seconds,
        quota_guard_enabled=quota_guard,
        quota_stop_ratio=quota_stop_ratio,
        quota_safety_multiplier=quota_safety_multiplier,
        audit_output=audit_output,
    )


def probe_tick_depth(
    *,
    provider: TickDataProvider,
    symbol: str,
    trade_date: str,
    output_root: str | Path,
    fields: Sequence[str] | None = None,
    adjust_type: str = "none",
    time_slice: str | None = None,
) -> dict[str, Any]:
    """Run a one-symbol one-day probe and return a compact summary."""
    metadata = download_tick_depth(
        provider=provider,
        symbols=[symbol],
        start_date=trade_date,
        end_date=trade_date,
        output_root=output_root,
        fields=fields,
        batch_size=1,
        resume=False,
        continue_on_error=False,
        metadata_kind="probe",
        calendar="calendar",
        adjust_type=adjust_type,
        time_slice=time_slice,
    )
    completed = metadata["completed_units"][0] if metadata["completed_units"] else {}
    summary = {
        "symbol": symbol,
        "trade_date": format_date(trade_date),
        "rows": metadata["rows"],
        "columns": completed.get("columns", []),
        "parquet_path": completed.get("part_path"),
        "metadata_path": metadata.get("metadata_path"),
    }
    if not metadata["rows"]:
        summary["warning"] = (
            "provider returned zero rows; check the trade date, symbol, suspension status, "
            "and account tick-history entitlement window"
        )

    if completed.get("part_path"):
        import pandas as pd

        df = pd.read_parquet(completed["part_path"])
        if "datetime" in df.columns and not df.empty:
            timestamps = pd.to_datetime(df["datetime"], errors="coerce")
            summary["first_timestamp"] = timestamps.min().isoformat()
            summary["last_timestamp"] = timestamps.max().isoformat()
        else:
            summary["first_timestamp"] = None
            summary["last_timestamp"] = None
    return summary


def provider_error_to_exit(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, ProviderRequestError):
        return 2, str(exc)
    return 1, str(exc)
