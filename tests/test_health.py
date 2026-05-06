from __future__ import annotations

import pandas as pd

from rqdata_tick_data.health import inspect_raw_health, write_health_report
from rqdata_tick_data.storage import atomic_write_parquet


def test_health_reports_duplicates_and_bad_quotes(tmp_path) -> None:
    root = tmp_path / "cache"
    path = root / "parts" / "trade_date=20250303" / "batch_0000.parquet"
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG", "00001.XHKG", "00001.XHKG"],
            "datetime": [
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:31"),
            ],
            "trading_date": ["20250303", "20250303", "20250303"],
            "a1": [100.1, 100.1, 99.0],
            "b1": [100.0, 100.0, 100.0],
            "volume": [100, 200, 150],
            "total_turnover": [10000, 20000, 15000],
        }
    )
    atomic_write_parquet(frame, path)
    report = inspect_raw_health(root)
    assert report["status"] == "pass"
    assert report["quality_verdict"]["overall_severity"] == "warning"
    assert report["quality_verdict"]["gate_status"] == "pass"
    assert report["duplicate_row_count"] == 2
    assert report["duplicate_key_count"] == 1
    assert report["invalid_best_spread_count"] == 1
    assert report["volume_decrease_count"] == 1

    written = write_health_report(root)
    assert written["report_path"]


def test_health_gate_can_fail_on_warnings(tmp_path) -> None:
    root = tmp_path / "cache"
    path = root / "parts" / "trade_date=20250303" / "batch_0000.parquet"
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG", "00001.XHKG"],
            "datetime": [
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:30"),
            ],
            "trading_date": ["20250303", "20250303"],
            "a1": [100.1, 100.1],
            "b1": [100.0, 100.0],
        }
    )
    atomic_write_parquet(frame, path)

    report = inspect_raw_health(root, fail_on_severity="warning")

    assert report["status"] == "pass"
    assert report["quality_verdict"]["gate_status"] == "fail"
