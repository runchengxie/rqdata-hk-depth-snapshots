"""Probe and download workflows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rqdata_tick_data.exceptions import DownloadError, ProviderRequestError
from rqdata_tick_data.fields import DEFAULT_TICK_DEPTH_FIELDS
from rqdata_tick_data.rq_client import TickDataProvider
from rqdata_tick_data.schema import normalize_tick_frame
from rqdata_tick_data.storage import (
    atomic_write_parquet,
    batch_part_path,
    metadata_path,
    write_json,
)
from rqdata_tick_data.symbols import format_date, iter_dates


@dataclass(frozen=True)
class BatchPlan:
    trade_date: str
    batch_number: int
    symbols: tuple[str, ...]
    part_path: Path


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
) -> list[BatchPlan]:
    root = Path(output_root)
    batches: list[BatchPlan] = []
    for trade_date in iter_dates(start_date, end_date):
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


def _base_metadata(
    *,
    kind: str,
    symbols: Sequence[str],
    start_date: str,
    end_date: str,
    fields: Sequence[str],
    output_root: str | Path,
    batch_size: int,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "provider": "rqdata",
        "market": "hk",
        "frequency": "tick",
        "start_date": format_date(start_date),
        "end_date": format_date(end_date),
        "symbols_requested": list(symbols),
        "fields_requested": list(fields),
        "batch_size": batch_size,
        "output_root": str(output_root),
        "created_at": utc_now_iso(),
        "completed_batches": [],
        "skipped_batches": [],
        "failed_batches": [],
        "rows": 0,
    }


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
) -> dict[str, Any]:
    """Download tick-depth snapshots into parquet parts and write run metadata."""
    selected_fields = list(fields or DEFAULT_TICK_DEPTH_FIELDS)
    root = Path(output_root)
    plans = build_batch_plan(symbols, start_date, end_date, root, batch_size)
    metadata = _base_metadata(
        kind=metadata_kind,
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        fields=selected_fields,
        output_root=root,
        batch_size=batch_size,
    )
    metadata["planned_batches"] = [
        {
            "trade_date": plan.trade_date,
            "batch_number": plan.batch_number,
            "symbols": list(plan.symbols),
            "part_path": str(plan.part_path),
        }
        for plan in plans
    ]
    metadata["dry_run"] = dry_run

    if dry_run:
        return metadata
    if provider is None:
        raise DownloadError("A provider is required unless dry_run=True.")

    metadata["quota_before"] = _quota_snapshot(provider)
    metadata_file = metadata_path(root, metadata_kind)

    try:
        for plan in plans:
            batch_info = {
                "trade_date": plan.trade_date,
                "batch_number": plan.batch_number,
                "symbols": list(plan.symbols),
                "part_path": str(plan.part_path),
            }
            if resume and plan.part_path.exists():
                metadata["skipped_batches"].append(batch_info)
                continue
            try:
                raw = provider.get_price(
                    order_book_ids=plan.symbols,
                    start_date=plan.trade_date,
                    end_date=plan.trade_date,
                    fields=selected_fields,
                )
                normalized = normalize_tick_frame(raw, selected_fields)
                atomic_write_parquet(normalized, plan.part_path)
                batch_info["rows"] = int(len(normalized))
                batch_info["columns"] = list(normalized.columns)
                metadata["rows"] += int(len(normalized))
                metadata["completed_batches"].append(batch_info)
            except Exception as exc:
                category = getattr(exc, "category", "download_error")
                failed_info = {**batch_info, "category": category, "error": str(exc)}
                metadata["failed_batches"].append(failed_info)
                if not continue_on_error:
                    raise
    finally:
        metadata["quota_after"] = _quota_snapshot(provider)
        write_json(metadata_file, metadata)
        metadata["metadata_path"] = str(metadata_file)

    if metadata["failed_batches"] and not continue_on_error:
        raise DownloadError("Download failed before completion.")
    return metadata


def probe_tick_depth(
    *,
    provider: TickDataProvider,
    symbol: str,
    trade_date: str,
    output_root: str | Path,
    fields: Sequence[str] | None = None,
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
    )
    completed = metadata["completed_batches"][0] if metadata["completed_batches"] else {}
    summary = {
        "symbol": symbol,
        "trade_date": format_date(trade_date),
        "rows": metadata["rows"],
        "columns": completed.get("columns", []),
        "parquet_path": completed.get("part_path"),
        "metadata_path": metadata.get("metadata_path"),
    }

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
