from __future__ import annotations

import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from rqdata_tick_data.cli import main
from rqdata_tick_data.compact import compact_raw_cache
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.storage import load_parquet_parts, symbol_date_part_path
from rqdata_tick_data.testing import FakeProvider


def _write_raw_across_quarters(root) -> None:
    download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250331",
        end_date="20250402",
        output_root=root,
        fields=parse_fields("last volume total_turnover a1 a1_v b1 b1_v"),
        batch_size=1,
        parquet_compression="zstd",
        parquet_compression_level=12,
    )


def test_compact_raw_quarter_merges_days_into_bounded_row_groups(tmp_path) -> None:
    source = tmp_path / "raw"
    output = tmp_path / "compact_quarter"
    _write_raw_across_quarters(source)

    report = compact_raw_cache(
        source,
        output,
        grouping="symbol-quarter",
        parquet_compression_level=12,
        row_group_days=2,
    )

    assert report["status"] == "pass"
    assert report["source_parts"] == 6
    assert report["compact_parts"] == 4
    assert report["layout_version"] == "compact_symbol_quarter.v1"
    assert report["row_group_days"] == 2
    q2 = output / "parts/order_book_id=00001.XHKG/year=2025/quarter=Q2.parquet"
    assert pq.ParquetFile(q2).metadata.num_row_groups == 1
    pd.testing.assert_frame_equal(
        load_parquet_parts(output).sort_values(["order_book_id", "datetime"], ignore_index=True),
        load_parquet_parts(source).sort_values(["order_book_id", "datetime"], ignore_index=True),
    )


def test_compact_raw_year_daily_row_groups_and_cli(tmp_path, capsys) -> None:
    source = tmp_path / "raw"
    output = tmp_path / "compact_year"
    _write_raw_across_quarters(source)

    code = main(
        [
            "compact-raw",
            "--input",
            str(source),
            "--output",
            str(output),
            "--grouping",
            "symbol-year",
            "--compression-level",
            "12",
            "--row-group-days",
            "1",
            "--progress",
        ]
    )

    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["compact_parts"] == 2
    target = output / "parts/order_book_id=00001.XHKG/year=2025.parquet"
    assert pq.ParquetFile(target).metadata.num_row_groups == 3


def test_compact_raw_unifies_empty_null_typed_source_parts(tmp_path) -> None:
    source = tmp_path / "raw"
    output = tmp_path / "compact"
    _write_raw_across_quarters(source)
    empty_path = symbol_date_part_path(source, "20250402", "00001.XHKG")
    field_names = list(reversed(pq.ParquetFile(empty_path).schema_arrow.names))
    pq.write_table(
        pa.table({name: pa.nulls(0) for name in field_names}),
        empty_path,
        compression="zstd",
        compression_level=12,
    )

    report = compact_raw_cache(source, output, row_group_days=2)

    assert report["status"] == "pass"
    assert report["schema_variant_compact_parts"] == 1
    target = output / "parts/order_book_id=00001.XHKG/year=2025/quarter=Q2.parquet"
    assert pq.ParquetFile(target).schema_arrow.field("last").type == pa.float64()


def test_compact_raw_rejects_overlapping_symbol_date_sources(tmp_path) -> None:
    first = tmp_path / "source" / "first"
    second = tmp_path / "source" / "second"
    _write_raw_across_quarters(first)
    second_part = symbol_date_part_path(second, "20250331", "00001.XHKG")
    second_part.parent.mkdir(parents=True, exist_ok=True)
    second_part.write_bytes(symbol_date_part_path(first, "20250331", "00001.XHKG").read_bytes())

    with pytest.raises(ValueError, match="duplicate symbol-date"):
        compact_raw_cache(tmp_path / "source", tmp_path / "compact")


def test_compact_raw_resolves_only_safe_duplicate_cases(tmp_path) -> None:
    source = tmp_path / "source"
    primary = source / "primary"
    output = tmp_path / "compact"
    _write_raw_across_quarters(primary)

    copied_from = symbol_date_part_path(primary, "20250331", "00700.XHKG")
    exact_copy = symbol_date_part_path(source / "copy", "20250331", "00700.XHKG")
    exact_copy.parent.mkdir(parents=True, exist_ok=True)
    exact_copy.write_bytes(copied_from.read_bytes())

    refetched = symbol_date_part_path(primary, "20250331", "00001.XHKG")
    retry_empty = symbol_date_part_path(source / "retry", "20250331", "00001.XHKG")
    retry_empty.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_batches([], schema=pq.ParquetFile(refetched).schema_arrow),
        retry_empty,
        compression="zstd",
        compression_level=12,
    )

    typed_schema = pq.ParquetFile(refetched).schema_arrow
    typed_empty = symbol_date_part_path(source / "typed_empty", "20250102", "09999.XHKG")
    null_empty = symbol_date_part_path(source / "null_empty", "20250102", "09999.XHKG")
    typed_empty.parent.mkdir(parents=True, exist_ok=True)
    null_empty.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_batches([], schema=typed_schema), typed_empty)
    pq.write_table(pa.table({field.name: pa.nulls(0) for field in typed_schema}), null_empty)

    report = compact_raw_cache(
        source,
        output,
        duplicate_policy="prefer-nonempty-identical",
    )

    duplicate_resolution = report["duplicate_resolution"]
    assert duplicate_resolution["duplicate_symbol_date_units"] == 3
    assert duplicate_resolution["dropped_duplicate_parts"] == 3
    assert duplicate_resolution["resolutions"] == {
        "byte_identical": 1,
        "all_empty_schema_or_metadata_diff": 1,
        "nonempty_replaces_empty": 1,
    }
    target = output / "parts/order_book_id=00001.XHKG/year=2025/quarter=Q1.parquet"
    assert pq.ParquetFile(target).metadata.num_rows == pq.ParquetFile(refetched).metadata.num_rows


def test_compact_raw_rejects_conflicting_nonempty_duplicates(tmp_path) -> None:
    source = tmp_path / "source"
    primary = source / "primary"
    _write_raw_across_quarters(primary)
    original = symbol_date_part_path(primary, "20250331", "00001.XHKG")
    conflicting = symbol_date_part_path(source / "conflict", "20250331", "00001.XHKG")
    conflicting.parent.mkdir(parents=True, exist_ok=True)
    changed = pq.read_table(original).to_pandas()
    changed.loc[0, "last"] += 1.0
    pq.write_table(pa.Table.from_pandas(changed, preserve_index=False), conflicting)

    with pytest.raises(ValueError, match="conflicting non-empty duplicate"):
        compact_raw_cache(
            source,
            tmp_path / "compact",
            duplicate_policy="prefer-nonempty-identical",
        )
