from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from rqdata_tick_data.cli import main
from rqdata_tick_data.coverage import scan_raw_coverage
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.storage import (
    DEFAULT_PARQUET_COMPRESSION,
    DEFAULT_PARQUET_COMPRESSION_LEVEL,
    atomic_write_parquet,
    batch_part_path,
    decode_order_book_id,
    encode_order_book_id,
    load_parquet_parts,
    metadata_path,
    symbol_date_part_path,
)
from rqdata_tick_data.testing import FakeProvider


class CountingProvider(FakeProvider):
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        self.calls.append(
            {
                "order_book_ids": tuple(order_book_ids),
                "start_date": start_date,
                "end_date": end_date,
                "fields": tuple(fields),
                "adjust_type": adjust_type,
                "time_slice": time_slice,
            }
        )
        return super().get_price(
            order_book_ids,
            start_date,
            end_date,
            fields,
            adjust_type,
            time_slice,
        )


class NoCallProvider(FakeProvider):
    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        raise AssertionError("provider should not be called")


class EmptyProvider(FakeProvider):
    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        return pd.DataFrame()


class IncrementingQuotaProvider(CountingProvider):
    def __init__(self) -> None:
        super().__init__()
        self.bytes_used = 100

    def quota_snapshot(self) -> dict[str, object]:
        return {
            "bytes_used": self.bytes_used,
            "bytes_limit": 1_000,
            "bytes_remaining": 1_000 - self.bytes_used,
        }

    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        frame = super().get_price(
            order_book_ids,
            start_date,
            end_date,
            fields,
            adjust_type,
            time_slice,
        )
        self.bytes_used += 800
        return frame


class FlakyProvider(CountingProvider):
    def __init__(self) -> None:
        super().__init__()
        self.failures_remaining = 1

    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        self.calls.append(
            {
                "order_book_ids": tuple(order_book_ids),
                "start_date": start_date,
                "end_date": end_date,
                "fields": tuple(fields),
                "adjust_type": adjust_type,
                "time_slice": time_slice,
            }
        )
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise RuntimeError("temporary provider timeout")
        return FakeProvider().get_price(
            order_book_ids,
            start_date,
            end_date,
            fields,
            adjust_type,
            time_slice,
        )


class AuditVisibleDuringRunProvider(CountingProvider):
    def __init__(self, audit_path) -> None:
        super().__init__()
        self.audit_path = audit_path
        self.observed_status: str | None = None

    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        if self.calls:
            self.observed_status = str(pd.read_csv(self.audit_path).loc[0, "status"])
        return super().get_price(
            order_book_ids,
            start_date,
            end_date,
            fields,
            adjust_type,
            time_slice,
        )


class MetadataVisibleDuringRunProvider(CountingProvider):
    def __init__(self, output_root) -> None:
        super().__init__()
        self.output_root = output_root
        self.observed_completed_batches: int | None = None
        self.observed_run_status: str | None = None

    def get_price(
        self,
        order_book_ids,
        start_date,
        end_date,
        fields,
        adjust_type="none",
        time_slice=None,
    ):
        if self.calls:
            paths = sorted((self.output_root / "meta").glob("download_*.json"))
            checkpoint = json.loads(paths[-1].read_text(encoding="utf-8"))
            self.observed_completed_batches = checkpoint["detail_counts"]["completed_batches"]
            self.observed_run_status = checkpoint["run_status"]
        return super().get_price(
            order_book_ids,
            start_date,
            end_date,
            fields,
            adjust_type,
            time_slice,
        )


def test_batch_path_and_metadata_path(tmp_path) -> None:
    root = tmp_path / "cache"
    assert batch_part_path(root, "20250303", 2) == (
        root / "parts" / "trade_date=20250303" / "batch_0002.parquet"
    )
    assert symbol_date_part_path(root, "20250303", "00001.XHKG") == (
        root / "parts" / "trade_date=20250303" / "order_book_id=00001.XHKG.parquet"
    )
    assert decode_order_book_id(encode_order_book_id("00001.XHKG/ALT")) == "00001.XHKG/ALT"
    assert metadata_path(root, "download", "stamp") == root / "meta" / "download_stamp.json"


def test_download_resume_skips_valid_existing_symbol_date_part(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    first = download_tick_depth(
        provider=CountingProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        resume=True,
    )
    second = download_tick_depth(
        provider=NoCallProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        resume=True,
    )
    assert first["rows"] == 4
    assert second["rows"] == 0
    assert len(second["skipped_batches"]) == 1
    assert len(second["skipped_units"]) == 1
    assert second["skipped_units"][0]["validation_status"] == "valid"
    assert symbol_date_part_path(root, "20250303", "00001.XHKG").exists()


def test_resume_redownloads_field_mismatch(tmp_path) -> None:
    root = tmp_path / "cache"
    initial_fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    expanded_fields = parse_fields("last volume total_turnover prev_close a1 a1_v b1 b1_v")
    download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=initial_fields,
        batch_size=1,
    )
    provider = CountingProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=expanded_fields,
        batch_size=1,
        resume=True,
    )
    assert len(provider.calls) == 1
    assert result["invalid_units"][0]["validation_status"] == "field_mismatch"
    assert result["rows"] == 4


def test_resume_accepts_existing_part_with_reordered_fields(tmp_path) -> None:
    root = tmp_path / "cache"
    requested_fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    provider_order = parse_fields("last volume total_turnover a1 b1 a1_v b1_v")
    frame = FakeProvider().get_price(
        ["00001.XHKG"],
        "20250303",
        "20250303",
        provider_order,
    )
    atomic_write_parquet(frame.reset_index(), symbol_date_part_path(root, "20250303", "00001.XHKG"))

    result = download_tick_depth(
        provider=NoCallProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=requested_fields,
        batch_size=1,
        resume=True,
    )

    assert result["audit_status_counts"]["skipped_existing"] == 1
    assert result["skipped_units"][0]["validation_status"] == "valid"


@pytest.mark.parametrize(
    ("frame", "expected_status"),
    [
        (
            pd.DataFrame(
                {
                    "order_book_id": ["00001.XHKG"],
                    "datetime": [pd.Timestamp("2025-03-03 09:30")],
                    "last": [100.0],
                }
            ),
            "schema_mismatch",
        ),
        (
            pd.DataFrame(
                {
                    "order_book_id": ["00700.XHKG"],
                    "datetime": [pd.Timestamp("2025-03-04 09:30")],
                    "trading_date": ["20250304"],
                    "last": [100.0],
                    "volume": [100],
                    "total_turnover": [10000.0],
                    "a1": [100.1],
                    "a1_v": [1000],
                    "b1": [99.9],
                    "b1_v": [900],
                }
            ),
            "identity_mismatch",
        ),
    ],
)
def test_resume_redownloads_schema_and_identity_mismatches(
    tmp_path,
    frame: pd.DataFrame,
    expected_status: str,
) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    path = symbol_date_part_path(root, "20250303", "00001.XHKG")
    atomic_write_parquet(frame, path)
    provider = CountingProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        resume=True,
    )
    assert len(provider.calls) == 1
    assert result["invalid_units"][0]["validation_status"] == expected_status


def test_resume_redownloads_unreadable_part(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    path = symbol_date_part_path(root, "20250303", "00001.XHKG")
    path.parent.mkdir(parents=True)
    path.write_text("not parquet", encoding="utf-8")
    provider = CountingProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        resume=True,
    )
    assert len(provider.calls) == 1
    assert result["invalid_units"][0]["validation_status"] == "unreadable"


def test_incremental_added_symbol_only_downloads_missing_unit(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=2,
    )
    provider = CountingProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=2,
        resume=True,
    )
    assert [call["order_book_ids"] for call in provider.calls] == [("00700.XHKG",)]
    assert len(result["skipped_units"]) == 1
    assert result["completed_units"][0]["order_book_id"] == "00700.XHKG"


def test_provider_calendar_skips_non_trading_dates(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    provider = CountingProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250301",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        calendar="provider",
    )
    assert result["trade_dates"] == ["20250303"]
    assert result["calendar_source"] == "provider"
    assert [call["start_date"] for call in provider.calls] == ["20250303"]


def test_calendar_mode_keeps_natural_days_for_offline_planning(tmp_path) -> None:
    result = download_tick_depth(
        provider=None,
        symbols=["00001.XHKG"],
        start_date="20250301",
        end_date="20250303",
        output_root=tmp_path / "cache",
        dry_run=True,
        calendar="calendar",
    )
    assert result["trade_dates"] == ["20250301", "20250302", "20250303"]
    assert result["calendar_source"] == "calendar"


def test_download_passes_raw_adjustment_and_time_slice(tmp_path) -> None:
    provider = CountingProvider()
    download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume"),
        adjust_type="none",
        time_slice="09:30:00-10:00:00",
    )
    assert provider.calls[0]["adjust_type"] == "none"
    assert provider.calls[0]["time_slice"] == "09:30:00-10:00:00"


def test_empty_provider_units_are_marked_in_metadata(tmp_path) -> None:
    result = download_tick_depth(
        provider=EmptyProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume"),
    )

    assert result["rows"] == 0
    assert result["empty_units"][0]["order_book_id"] == "00001.XHKG"
    assert result["audit_status_counts"]["empty_remote"] == 1
    audit = pd.read_csv(result["audit_path"])
    assert audit.loc[0, "status"] == "empty_remote"


def test_download_writes_audit_for_written_and_resume_skipped_units(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    first = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
    )
    second = download_tick_depth(
        provider=NoCallProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        resume=True,
    )

    assert first["audit_status_counts"]["written"] == 1
    assert pd.read_csv(first["audit_path"]).loc[0, "status"] == "written"
    assert second["audit_status_counts"]["skipped_existing"] == 1
    assert pd.read_csv(second["audit_path"]).loc[0, "status"] == "skipped_existing"


def test_download_persists_audit_before_requesting_the_next_batch(tmp_path) -> None:
    audit_path = tmp_path / "download_audit.csv"
    provider = AuditVisibleDuringRunProvider(audit_path)

    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        audit_output=audit_path,
    )

    assert provider.observed_status == "written"
    assert result["audit_status_counts"]["written"] == 2
    assert list(pd.read_csv(audit_path)["status"]) == ["written", "written"]


def test_download_bounds_inline_metadata_and_streams_full_details(tmp_path) -> None:
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG", "00700.XHKG", "00941.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        metadata_detail_limit=1,
    )

    detail_rows = [
        json.loads(line)
        for line in Path(result["detail_records_path"]).read_text(encoding="utf-8").splitlines()
    ]
    completed_details = [
        row for row in detail_rows if row["collection"] == "completed_units"
    ]

    assert result["detail_inline_limit"] == 1
    assert result["detail_counts"]["completed_units"] == 3
    assert len(result["completed_units"]) == 1
    assert "completed_units" in result["detail_lists_truncated"]
    assert len(completed_details) == 3
    assert result["run_status"] == "complete"


def test_download_checkpoints_bounded_metadata_between_batches(tmp_path) -> None:
    root = tmp_path / "cache"
    provider = MetadataVisibleDuringRunProvider(root)

    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        metadata_detail_limit=1,
    )

    assert provider.observed_completed_batches == 1
    assert provider.observed_run_status == "running"
    assert result["detail_counts"]["completed_batches"] == 2
    assert len(result["completed_batches"]) == 1


def test_quota_guard_blocks_next_chunk_without_provider_call(tmp_path) -> None:
    provider = IncrementingQuotaProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        quota_stop_ratio=0.95,
        quota_safety_multiplier=1.2,
    )
    audit = pd.read_csv(result["audit_path"])

    assert len(provider.calls) == 1
    assert result["audit_status_counts"]["written"] == 1
    assert result["audit_status_counts"]["quota_blocked"] == 1
    assert set(audit["status"]) == {"written", "quota_blocked"}
    assert len(load_parquet_parts(tmp_path / "cache")) == 4


def test_retry_metadata_records_attempts(tmp_path) -> None:
    provider = FlakyProvider()
    result = download_tick_depth(
        provider=provider,
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        retry_max_attempts=2,
        retry_backoff_seconds=0,
    )
    audit = pd.read_csv(result["audit_path"])

    assert len(provider.calls) == 2
    assert result["completed_units"][0]["attempts"] == 2
    assert audit.loc[0, "attempts"] == 2


def test_batched_provider_response_writes_symbol_date_parts(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=2,
    )
    assert result["rows"] == 8
    assert len(result["completed_batches"]) == 1
    assert len(result["completed_units"]) == 2
    assert symbol_date_part_path(root, "20250303", "00001.XHKG").exists()
    assert symbol_date_part_path(root, "20250303", "00700.XHKG").exists()
    assert not batch_part_path(root, "20250303", 0).exists()


def test_legacy_batch_download_records_deprecation(tmp_path) -> None:
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        raw_layout="batch",
    )

    assert result["deprecations"][0]["feature"] == "raw_layout=batch"
    assert result["deprecations"][0]["replacement"] == "raw_layout=symbol-date"


def test_default_parquet_compression_recorded_in_metadata_and_coverage(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
    )
    rows = scan_raw_coverage(root, requested_fields=fields)
    assert result["parquet"]["compression"] == DEFAULT_PARQUET_COMPRESSION
    assert result["parquet"]["compression_level"] == DEFAULT_PARQUET_COMPRESSION_LEVEL
    assert {row["compression"] for row in rows} == {DEFAULT_PARQUET_COMPRESSION}


def test_explicit_parquet_compression_recorded_in_metadata_and_coverage(tmp_path) -> None:
    root = tmp_path / "cache"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        parquet_compression="zstd",
        parquet_compression_level=3,
    )
    rows = scan_raw_coverage(root, requested_fields=fields)
    assert result["parquet"]["compression"] == "zstd"
    assert result["parquet"]["compression_level"] == 3
    assert {row["compression"] for row in rows} == {"zstd"}


def test_snappy_without_compression_level_remains_supported(tmp_path) -> None:
    result = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=tmp_path / "cache",
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        parquet_compression="snappy",
    )

    assert result["parquet"]["compression"] == "snappy"
    assert result["parquet"]["compression_level"] is None


def test_unsupported_parquet_options_fail_before_writing(tmp_path) -> None:
    with pytest.raises(ValueError, match="Unsupported parquet compression"):
        download_tick_depth(
            provider=None,
            symbols=["00001.XHKG"],
            start_date="20250303",
            end_date="20250303",
            output_root=tmp_path / "cache",
            dry_run=True,
            parquet_compression="bad-codec",
        )


def test_cli_download_dry_run_and_fake_provider(tmp_path, capsys) -> None:
    dry_code = main(
        [
            "download",
            "--symbols",
            "00001.XHKG,00700.XHKG",
            "--start-date",
            "20250303",
            "--end-date",
            "20250303",
            "--out",
            str(tmp_path / "dry"),
            "--batch-size",
            "1",
            "--dry-run",
        ]
    )
    assert dry_code == 0
    dry_output = json.loads(capsys.readouterr().out)
    assert len(dry_output["planned_batches"]) == 2

    out = tmp_path / "cache"
    code = main(
        [
            "download",
            "--symbols",
            "00001.XHKG",
            "--start-date",
            "20250303",
            "--end-date",
            "20250303",
            "--out",
            str(out),
            "--fields",
            "last volume total_turnover a1 a1_v b1 b1_v",
            "--fake-provider",
        ]
    )
    assert code == 0
    assert symbol_date_part_path(out, "20250303", "00001.XHKG").exists()


def test_cli_quota_fake_provider_pretty(capsys) -> None:
    code = main(["quota", "--fake-provider", "--pretty"])

    assert code == 0
    output = capsys.readouterr().out
    assert "Quota usage" in output
    assert "bytes_remaining" in output
