"""Download audit records and summaries."""

from __future__ import annotations

import os
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from rqdata_tick_data.storage import now_stamp

AUDIT_STATUSES = (
    "planned",
    "written",
    "skipped_existing",
    "empty_remote",
    "failed",
    "quota_blocked",
)
TERMINAL_AUDIT_STATUSES = tuple(status for status in AUDIT_STATUSES if status != "planned")


@dataclass(frozen=True)
class AuditRecord:
    """One symbol-date audit row."""

    run_id: str
    chunk_id: str
    trade_date: str
    order_book_id: str
    status: str
    part_path: str
    rows: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_seconds: float | None = None
    quota_before_bytes_used: int | None = None
    quota_after_bytes_used: int | None = None
    quota_delta_bytes: int | None = None
    attempts: int | None = None
    error_type: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        if self.status not in AUDIT_STATUSES:
            raise ValueError(f"Unsupported audit status: {self.status}")
        return asdict(self)


def default_audit_path(dataset_root: str | Path, kind: str = "download") -> Path:
    return Path(dataset_root) / "audit" / f"{kind}_{now_stamp()}_{uuid.uuid4().hex[:8]}.csv"


def write_audit_records(path: str | Path, records: list[AuditRecord | dict[str, Any]]) -> Path:
    """Write audit rows through a temporary file and atomic rename."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        record.to_dict() if isinstance(record, AuditRecord) else dict(record)
        for record in records
    ]
    frame = pd.DataFrame(rows)
    for column in AuditRecord.__dataclass_fields__:
        if column not in frame.columns:
            frame[column] = pd.NA
    frame = frame[list(AuditRecord.__dataclass_fields__)]
    temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        frame.to_csv(temp, index=False)
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()
    return target


def summarize_audit(records: list[AuditRecord | dict[str, Any]]) -> dict[str, int]:
    """Count terminal audit statuses."""
    counts: Counter[str] = Counter()
    for record in records:
        status = record.status if isinstance(record, AuditRecord) else str(record.get("status"))
        if status in TERMINAL_AUDIT_STATUSES:
            counts[status] += 1
    return {status: int(counts.get(status, 0)) for status in TERMINAL_AUDIT_STATUSES}


def read_audit_records(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
