from __future__ import annotations

import pytest

from rqdata_tick_data.audit import (
    AuditRecord,
    IncrementalAuditWriter,
    read_audit_records,
    summarize_audit,
    write_audit_records,
)
from rqdata_tick_data.exceptions import ProviderRequestError
from rqdata_tick_data.runtime import looks_like_quota_error, retry_provider_call


def test_quota_error_classification() -> None:
    assert looks_like_quota_error(Exception("traffic quota exceeded limit"))
    assert looks_like_quota_error(Exception("流量配额已用完"))
    assert not looks_like_quota_error(Exception("temporary provider timeout"))


def test_retry_provider_call_succeeds_after_transient_error() -> None:
    attempts = {"count": 0}

    def action() -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary provider timeout")
        return "ok"

    result = retry_provider_call("probe", action, max_attempts=2, backoff_seconds=0)

    assert result.value == "ok"
    assert result.attempts == 2


def test_retry_provider_call_stops_on_quota_error() -> None:
    def action() -> str:
        raise RuntimeError("bytes_limit exceeded")

    with pytest.raises(ProviderRequestError) as exc_info:
        retry_provider_call("probe", action, max_attempts=3, backoff_seconds=0)

    assert exc_info.value.category == "quota"


def test_retry_provider_call_raises_after_exhaustion() -> None:
    with pytest.raises(ProviderRequestError) as exc_info:
        retry_provider_call(
            "probe",
            lambda: (_ for _ in ()).throw(RuntimeError("temporary provider timeout")),
            max_attempts=2,
            backoff_seconds=0,
        )

    assert exc_info.value.category == "provider_error"


def test_audit_writer_and_summary(tmp_path) -> None:
    records = [
        AuditRecord(
            run_id="run",
            chunk_id="20250303:0000",
            trade_date="20250303",
            order_book_id="00001.XHKG",
            status="written",
            part_path="part.parquet",
            rows=4,
        ),
        AuditRecord(
            run_id="run",
            chunk_id="20250303:0001",
            trade_date="20250303",
            order_book_id="00700.XHKG",
            status="quota_blocked",
            part_path="part2.parquet",
        ),
    ]
    path = write_audit_records(tmp_path / "audit.csv", records)
    frame = read_audit_records(path)

    assert list(frame["status"]) == ["written", "quota_blocked"]
    assert summarize_audit(records)["written"] == 1
    assert summarize_audit(records)["quota_blocked"] == 1


def test_incremental_audit_writer_exposes_completed_batches_immediately(tmp_path) -> None:
    path = tmp_path / "audit.csv"
    writer = IncrementalAuditWriter(path)
    written = AuditRecord(
        run_id="run",
        chunk_id="20250303:0000",
        trade_date="20250303",
        order_book_id="00001.XHKG",
        status="written",
        part_path="part.parquet",
        rows=4,
    )
    failed = AuditRecord(
        run_id="run",
        chunk_id="20250303:0001",
        trade_date="20250303",
        order_book_id="00700.XHKG",
        status="failed",
        part_path="part2.parquet",
    )

    writer.append([written])
    assert list(read_audit_records(path)["status"]) == ["written"]

    writer.append([failed])
    assert list(read_audit_records(path)["status"]) == ["written", "failed"]
    assert writer.summary()["written"] == 1
    assert writer.summary()["failed"] == 1
