from __future__ import annotations

import pandas as pd

from rqdata_tick_data.aggregate import aggregate_daily_frame, write_daily_aggregate
from rqdata_tick_data.assets import emit_daily_asset, emit_raw_asset
from rqdata_tick_data.cli import main
from rqdata_tick_data.downloader import download_tick_depth
from rqdata_tick_data.fields import parse_fields
from rqdata_tick_data.health import write_health_report
from rqdata_tick_data.storage import load_parquet_parts
from rqdata_tick_data.testing import FakeProvider


def test_aggregate_metrics() -> None:
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG", "00001.XHKG"],
            "datetime": [pd.Timestamp("2025-03-03 09:30"), pd.Timestamp("2025-03-03 09:40")],
            "trading_date": ["20250303", "20250303"],
            "a1": [100.1, 100.2],
            "a1_v": [1000, 1100],
            "b1": [99.9, 100.0],
            "b1_v": [900, 1000],
            "volume": [1000, 2500],
            "total_turnover": [100000, 250300],
        }
    )
    out = aggregate_daily_frame(frame)
    assert len(out) == 1
    assert out.loc[0, "tick_count"] == 2
    assert out.loc[0, "spread_bps_p50"] > 0
    assert out.loc[0, "depth1_notional_p50"] > 0
    assert out.loc[0, "full_day_tick_vwap"] > 0


def test_offline_end_to_end_and_assets(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    aggregate_path = tmp_path / "daily" / "data.parquet"
    fields = parse_fields("last volume total_turnover a1 a1_v b1 b1_v")
    metadata = download_tick_depth(
        provider=FakeProvider(),
        symbols=["00001.XHKG", "00700.XHKG"],
        start_date="20250303",
        end_date="20250303",
        output_root=raw_root,
        fields=fields,
        batch_size=1,
    )
    assert metadata["rows"] == 8
    assert len(load_parquet_parts(raw_root)) == 8

    health = write_health_report(raw_root)
    assert health["status"] == "pass"

    aggregate_meta = write_daily_aggregate(raw_root, aggregate_path)
    assert aggregate_meta["rows"] == 2
    assert aggregate_path.exists()

    raw_asset = emit_raw_asset(raw_root, tmp_path / "asset_raw")
    daily_asset = emit_daily_asset(aggregate_path, tmp_path / "asset_daily")
    assert raw_asset["row_count"] == 8
    assert daily_asset["row_count"] == 2
    assert (tmp_path / "asset_raw" / "manifest.yml").exists()
    assert (tmp_path / "asset_daily" / "manifest.yml").exists()


def test_cli_offline_end_to_end(tmp_path) -> None:
    raw_root = tmp_path / "cli_raw"
    daily_path = tmp_path / "cli_daily" / "data.parquet"
    assert (
        main(
            [
                "download",
                "--symbols",
                "00001.XHKG",
                "--start-date",
                "20250303",
                "--end-date",
                "20250303",
                "--out",
                str(raw_root),
                "--fields",
                "last volume total_turnover a1 a1_v b1 b1_v",
                "--fake-provider",
            ]
        )
        == 0
    )
    assert main(["health", "--input", str(raw_root)]) == 0
    assert main(["aggregate-daily", "--input", str(raw_root), "--output", str(daily_path)]) == 0
    assert (
        main(
            [
                "emit-asset",
                "--kind",
                "daily",
                "--source",
                str(daily_path),
                "--output",
                str(tmp_path / "cli_asset_daily"),
            ]
        )
        == 0
    )
