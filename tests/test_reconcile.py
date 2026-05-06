from __future__ import annotations

import pandas as pd

from rqdata_tick_data.cli import main
from rqdata_tick_data.reconcile import (
    aggregate_tick_ohlcv,
    inspect_tick_daily_reconciliation,
)
from rqdata_tick_data.storage import atomic_write_parquet


def _write_raw(root, frame: pd.DataFrame) -> None:  # noqa: ANN001
    atomic_write_parquet(frame, root / "parts" / "trade_date=20250303" / "batch_0000.parquet")


def _write_daily(asset_root, symbol: str, frame: pd.DataFrame) -> None:  # noqa: ANN001
    atomic_write_parquet(frame, asset_root / "data" / f"{symbol}.parquet")


def test_tick_ohlcv_aggregation_uses_final_cumulative_fallback() -> None:
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG", "00001.XHKG", "00001.XHKG"],
            "datetime": [
                pd.Timestamp("2025-03-03 09:30"),
                pd.Timestamp("2025-03-03 09:31"),
                pd.Timestamp("2025-03-03 09:32"),
            ],
            "trading_date": ["20250303", "20250303", "20250303"],
            "last": [100.0, 101.0, 102.0],
            "volume": [100.0, 200.0, pd.NA],
            "total_turnover": [10000.0, 20100.0, pd.NA],
        }
    )

    aggregate, metadata = aggregate_tick_ohlcv(frame)

    assert aggregate.loc[0, "tick_close"] == 102.0
    assert aggregate.loc[0, "tick_volume"] == 200.0
    assert aggregate.loc[0, "tick_total_turnover"] == 20100.0
    assert metadata["volume_fallback_count"] == 1
    assert metadata["turnover_fallback_count"] == 1


def test_tick_ohlcv_aggregation_counts_invalid_timestamps() -> None:
    frame = pd.DataFrame(
        {
            "order_book_id": ["00001.XHKG"],
            "datetime": ["not-a-timestamp"],
            "trading_date": ["20250303"],
            "last": [100.0],
        }
    )

    _, metadata = aggregate_tick_ohlcv(frame)

    assert metadata["timestamp_parse_failure_count"] == 1


def test_reconciliation_matches_daily_reference_with_alias_mapping(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    daily_root = tmp_path / "daily"
    _write_raw(
        raw_root,
        pd.DataFrame(
            {
                "order_book_id": ["00001.XHKG", "00001.XHKG"],
                "datetime": [
                    pd.Timestamp("2025-03-03 09:30"),
                    pd.Timestamp("2025-03-03 16:08"),
                ],
                "trading_date": ["20250303", "20250303"],
                "last": [100.0, 101.0],
                "volume": [100.0, 200.0],
                "total_turnover": [10000.0, 20100.0],
                "a1": [100.1, 101.1],
                "b1": [99.9, 100.9],
            }
        ),
    )
    _write_daily(
        daily_root,
        "00001.HK",
        pd.DataFrame(
            {
                "trade_date": ["20250303"],
                "symbol": ["00001.HK"],
                "order_book_id": ["00001.XHKG"],
                "open": [100.0],
                "high": [101.0],
                "low": [100.0],
                "close": [101.0],
                "volume": [200.0],
                "total_turnover": [20100.0],
            }
        ),
    )

    report = inspect_tick_daily_reconciliation(raw_root, daily_root)

    assert report["summary"]["matched_symbol_days"] == 1
    assert not report["quality_checks"]


def test_reconciliation_reports_close_mismatch_and_quote_ladder(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    daily_root = tmp_path / "daily"
    _write_raw(
        raw_root,
        pd.DataFrame(
            {
                "order_book_id": ["00001.XHKG"],
                "datetime": [pd.Timestamp("2025-03-03 09:30")],
                "trading_date": ["20250303"],
                "last": [100.0],
                "volume": [100.0],
                "total_turnover": [10000.0],
                "a1": [99.0],
                "b1": [100.0],
            }
        ),
    )
    _write_daily(
        daily_root,
        "00001.HK",
        pd.DataFrame(
            {
                "trade_date": ["20250303"],
                "symbol": ["00001.HK"],
                "open": [101.0],
                "high": [101.0],
                "low": [101.0],
                "close": [101.0],
                "volume": [100.0],
                "total_turnover": [10000.0],
            }
        ),
    )

    report = inspect_tick_daily_reconciliation(raw_root, daily_root)
    checks = {check["check"] for check in report["quality_checks"]}

    assert "tick_close_mismatch" in checks
    assert "quote_ladder_invalid" in checks


def test_reconciliation_reports_active_daily_missing_tick(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    daily_root = tmp_path / "daily"
    _write_raw(
        raw_root,
        pd.DataFrame(
            {
                "order_book_id": ["00001.XHKG", "00700.XHKG"],
                "datetime": [
                    pd.Timestamp("2025-03-03 09:30"),
                    pd.Timestamp("2025-03-04 09:30"),
                ],
                "trading_date": ["20250303", "20250304"],
                "last": [100.0, 200.0],
                "volume": [100.0, 100.0],
                "total_turnover": [10000.0, 20000.0],
            }
        ),
    )
    _write_daily(
        daily_root,
        "00001.HK",
        pd.DataFrame(
            {
                "trade_date": ["20250303", "20250304"],
                "symbol": ["00001.HK", "00001.HK"],
                "open": [100.0, 101.0],
                "high": [100.0, 101.0],
                "low": [100.0, 101.0],
                "close": [100.0, 101.0],
                "volume": [100.0, 100.0],
                "total_turnover": [10000.0, 10100.0],
            }
        ),
    )
    _write_daily(
        daily_root,
        "00700.HK",
        pd.DataFrame(
            {
                "trade_date": ["20250304"],
                "symbol": ["00700.HK"],
                "open": [200.0],
                "high": [200.0],
                "low": [200.0],
                "close": [200.0],
                "volume": [100.0],
                "total_turnover": [20000.0],
            }
        ),
    )

    report = inspect_tick_daily_reconciliation(raw_root, daily_root)
    checks = {check["check"] for check in report["quality_checks"]}

    assert "daily_active_missing_tick" in checks


def test_reconcile_daily_cli_writes_report_and_gates_on_warning(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    daily_root = tmp_path / "daily"
    out = tmp_path / "report.json"
    _write_raw(
        raw_root,
        pd.DataFrame(
            {
                "order_book_id": ["00001.XHKG"],
                "datetime": [pd.Timestamp("2025-03-03 09:30")],
                "trading_date": ["20250303"],
                "last": [100.0],
                "volume": [100.0],
                "total_turnover": [10000.0],
            }
        ),
    )
    _write_daily(
        daily_root,
        "00001.HK",
        pd.DataFrame(
            {
                "trade_date": ["20250303"],
                "symbol": ["00001.HK"],
                "open": [101.0],
                "high": [101.0],
                "low": [101.0],
                "close": [101.0],
                "volume": [100.0],
                "total_turnover": [10000.0],
            }
        ),
    )

    code = main(
        [
            "reconcile-daily",
            "--tick-input",
            str(raw_root),
            "--daily-asset-dir",
            str(daily_root),
            "--out",
            str(out),
            "--fail-on-severity",
            "warning",
        ]
    )

    assert code == 2
    assert out.exists()
