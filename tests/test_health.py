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


def test_health_reports_symbol_date_diagnostics_and_split_anomalies(tmp_path) -> None:
    root = tmp_path / "cache"
    path = root / "parts" / "trade_date=20250303" / "batch_0000.parquet"
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG"] * 8,
            "datetime": [
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:31"),
                pd.Timestamp("2025-03-03 09:31"),
                pd.Timestamp("2025-03-03 09:31:30"),
                pd.Timestamp("2025-03-03 09:29"),
                pd.Timestamp("2025-03-03 08:59"),
                pd.Timestamp("2025-03-03 09:32"),
            ],
            "trading_date": ["20250303"] * 8,
            "last": [100.0, 100.0, 100.1, 100.2, 100.15, 100.0, 99.9, 100.3],
            "a1": [100.1, 100.1, 99.0, 101.0, 100.2, pd.NA, 100.0, 100.3],
            "a2": [100.2, 100.2, 99.2, 100.5, 100.3, pd.NA, 100.1, 100.4],
            "a1_v": [1000, 1000, 1000, -1, 1000, 1000, 1000, 1000],
            "b1": [100.0, 100.0, 100.0, 100.0, 100.1, 100.0, 0, 100.2],
            "b2": [99.9, 99.9, 99.8, 100.5, 100.0, 99.9, 99.8, 100.1],
            "b1_v": [900, 900, 900, 900, 900, 900, 900, 900],
            "volume": [100.0, 100.0, 200.0, 150.0, pd.NA, 1.0, 15.0, 20.0],
            "total_turnover": [
                10000.0,
                10000.0,
                20000.0,
                15000.0,
                pd.NA,
                100.0,
                1500.0,
                2000.0,
            ],
        }
    )
    atomic_write_parquet(frame, path)

    report = inspect_raw_health(root, fail_on_severity="warning")
    unit = report["unit_diagnostics"][0]

    assert report["best_ask_missing_count"] == 1
    assert report["best_bid_missing_count"] == 1
    assert report["best_spread_cross_count"] == 1
    assert report["ask_ladder_inversion_count"] == 1
    assert report["bid_ladder_inversion_count"] == 1
    assert report["negative_depth_volume_count"] == 1
    assert report["same_timestamp_conflict_count"] == 1
    assert report["timestamp_non_monotonic_count"] >= 1
    assert report["volume_large_drop_count"] >= 1
    assert report["volume_missing_then_resumed_count"] == 1
    assert report["outside_session_rows"] == 1
    assert unit["severity"] == "warning"
    assert "same_timestamp_conflicts" in unit["check_names"]
    assert report["quality_verdict"]["gate_status"] == "fail"


def test_health_can_write_unit_diagnostics(tmp_path) -> None:
    root = tmp_path / "cache"
    path = root / "parts" / "trade_date=20250303" / "batch_0000.parquet"
    atomic_write_parquet(
        pd.DataFrame(
            {
                "order_book_id": ["00001.XHKG"],
                "datetime": [pd.Timestamp("2025-03-03 09:30")],
                "trading_date": ["20250303"],
                "a1": [100.1],
                "b1": [100.0],
            }
        ),
        path,
    )

    report = write_health_report(root, units_output=tmp_path / "health_units.csv")

    assert report["unit_diagnostics_path"].endswith("health_units.csv")
    assert report["unit_diagnostics_write_mode"] == "streamed_csv"
    assert len(pd.read_csv(tmp_path / "health_units.csv")) == 1


def test_health_bounds_json_anomaly_samples_and_streams_full_unit_csv(tmp_path) -> None:
    root = tmp_path / "cache"
    for index, symbol in enumerate(("00001.XHKG", "00002.XHKG", "00003.XHKG"), start=1):
        path = root / "parts" / "trade_date=20250303" / f"part_{index}.parquet"
        atomic_write_parquet(
            pd.DataFrame(
                {
                    "order_book_id": [symbol, symbol],
                    "datetime": [
                        pd.Timestamp("2025-03-03 09:30"),
                        pd.Timestamp("2025-03-03 09:30"),
                    ],
                    "trading_date": ["20250303", "20250303"],
                    "a1": [100.1, 100.1],
                    "b1": [100.0, 100.0],
                }
            ),
            path,
        )

    units_path = tmp_path / "health_units.csv"
    report = write_health_report(
        root,
        units_output=units_path,
        unit_sample_limit=1,
    )

    assert report["unit_count"] == 3
    assert report["anomalous_unit_count"] == 3
    assert len(report["unit_diagnostics"]) == 1
    assert report["unit_diagnostics_truncated"] is True
    assert report["duplicate_key_count"] == 3
    assert report["unit_diagnostics_write_mode"] == "streamed_csv"
    assert len(pd.read_csv(units_path)) == 3


def test_health_empty_input_reports_unit_output_mode(tmp_path) -> None:
    units_path = tmp_path / "health_units.PARQUET"

    report = write_health_report(tmp_path / "cache", units_output=units_path)

    assert report["status"] == "fail"
    assert report["unit_diagnostics_write_mode"] == "buffered_parquet"
    assert report["unit_diagnostics_path"] == str(units_path)
    assert units_path.exists()
