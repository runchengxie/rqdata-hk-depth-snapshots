from __future__ import annotations

import json

import pandas as pd
import pytest

from rqdata_tick_data.cli import main
from rqdata_tick_data.coverage import scan_raw_coverage
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.storage import (
    atomic_write_parquet,
    batch_part_path,
    decode_order_book_id,
    encode_order_book_id,
    metadata_path,
    symbol_date_part_path,
)
from rqdata_tick_data.testing import FakeProvider


class CountingProvider(FakeProvider):
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def get_price(self, order_book_ids, start_date, end_date, fields):  # noqa: ANN001
        self.calls.append(
            {
                "order_book_ids": tuple(order_book_ids),
                "start_date": start_date,
                "end_date": end_date,
                "fields": tuple(fields),
            }
        )
        return super().get_price(order_book_ids, start_date, end_date, fields)


class NoCallProvider(FakeProvider):
    def get_price(self, order_book_ids, start_date, end_date, fields):  # noqa: ANN001
        raise AssertionError("provider should not be called")


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


def test_parquet_compression_recorded_in_metadata_and_coverage(tmp_path) -> None:
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
