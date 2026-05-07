from __future__ import annotations

import json

import pandas as pd

from rqdata_tick_data.cli import main
from rqdata_tick_data.coverage import scan_raw_coverage
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.health import write_health_report
from rqdata_tick_data.recompress import recompress_raw_cache
from rqdata_tick_data.storage import load_parquet_parts
from rqdata_tick_data.testing import FakeProvider


def _write_snappy_raw(root) -> list[str]:  # noqa: ANN001
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=root,
        fields=fields,
        batch_size=1,
        parquet_compression="snappy",
    )
    return fields


def test_recompress_raw_cache_preserves_rows_and_writes_report(tmp_path) -> None:
    source = tmp_path / "raw_snappy"
    output = tmp_path / "raw_zstd"
    fields = _write_snappy_raw(source)

    report = recompress_raw_cache(source, output)

    assert report["status"] == "pass"
    assert report["source_parts"] == 2
    assert report["rewritten_parts"] == 2
    assert report["copied_parts"] == 0
    assert report["parquet"]["compression"] == "zstd"
    assert report["parquet"]["compression_level"] == 3
    assert (output / "parts").exists()
    assert (output / "audit").exists()
    assert (output / "meta").exists()

    source_frame = load_parquet_parts(source).sort_values(
        ["order_book_id", "datetime"],
        ignore_index=True,
    )
    output_frame = load_parquet_parts(output).sort_values(
        ["order_book_id", "datetime"],
        ignore_index=True,
    )
    pd.testing.assert_frame_equal(output_frame, source_frame)

    rows = scan_raw_coverage(output, requested_fields=fields)
    assert {row["compression"] for row in rows} == {"zstd"}
    assert write_health_report(output)["status"] == "pass"


def test_recompress_raw_cache_can_copy_small_parts_below_threshold(tmp_path) -> None:
    source = tmp_path / "raw_snappy"
    output = tmp_path / "raw_mixed"
    _write_snappy_raw(source)

    report = recompress_raw_cache(source, output, min_rewrite_bytes=10**9)

    assert report["status"] == "pass"
    assert report["rewritten_parts"] == 0
    assert report["copied_parts"] == 2
    rows = scan_raw_coverage(output)
    assert {row["compression"] for row in rows} == {"snappy"}


def test_recompress_raw_cli(tmp_path, capsys) -> None:
    source = tmp_path / "raw_snappy"
    output = tmp_path / "raw_zstd"
    _write_snappy_raw(source)

    code = main(
        [
            "recompress-raw",
            "--input",
            str(source),
            "--output",
            str(output),
        ]
    )

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    assert payload["rewritten_parts"] == 2
    assert {row["compression"] for row in scan_raw_coverage(output)} == {"zstd"}
