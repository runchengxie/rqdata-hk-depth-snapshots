from __future__ import annotations

import json

from rqdata_tick_data.cli import main
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.storage import batch_part_path, metadata_path
from rqdata_tick_data.testing import FakeProvider


def test_batch_path_and_metadata_path(tmp_path) -> None:
    root = tmp_path / "cache"
    assert batch_part_path(root, "20250303", 2) == (
        root / "parts" / "trade_date=20250303" / "batch_0002.parquet"
    )
    assert metadata_path(root, "download", "stamp") == root / "meta" / "download_stamp.json"


def test_download_resume_skips_existing_part(tmp_path) -> None:
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
        resume=True,
    )
    second = download_tick_depth(
        provider=FakeProvider(),
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
    assert batch_part_path(root, "20250303", 0).exists()


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
    assert batch_part_path(out, "20250303", 0).exists()
