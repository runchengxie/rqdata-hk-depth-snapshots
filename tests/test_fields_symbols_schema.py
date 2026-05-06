from __future__ import annotations

import pandas as pd

from rqdata_tick_data.fields import DEFAULT_TICK_DEPTH_FIELDS, parse_fields
from rqdata_tick_data.schema import normalize_tick_frame
from rqdata_tick_data.symbols import (
    format_date,
    iter_dates,
    normalize_hk_order_book_id,
    parse_symbols,
)


def test_default_fields_include_ten_levels() -> None:
    assert "open" in DEFAULT_TICK_DEPTH_FIELDS
    assert "last" in DEFAULT_TICK_DEPTH_FIELDS
    assert "change_rate" in DEFAULT_TICK_DEPTH_FIELDS
    assert "a10" in DEFAULT_TICK_DEPTH_FIELDS
    assert "a10_v" in DEFAULT_TICK_DEPTH_FIELDS
    assert "b10" in DEFAULT_TICK_DEPTH_FIELDS
    assert "b10_v" in DEFAULT_TICK_DEPTH_FIELDS
    assert parse_fields("last, volume total_turnover,last") == [
        "last",
        "volume",
        "total_turnover",
    ]


def test_parse_symbols_from_text_and_file(tmp_path) -> None:
    symbols_file = tmp_path / "symbols.txt"
    symbols_file.write_text("# comment\n00700.XHKG\n00001.XHKG, 00941.XHKG\n", encoding="utf-8")
    symbols = parse_symbols("00001.XHKG, 00005.XHKG", symbols_file)
    assert symbols == ["00001.XHKG", "00005.XHKG", "00700.XHKG", "00941.XHKG"]


def test_parse_symbols_normalizes_hk_aliases_and_table_files(tmp_path) -> None:
    assert normalize_hk_order_book_id("700") == "00700.XHKG"
    assert normalize_hk_order_book_id("00700.HK") == "00700.XHKG"

    symbols_file = tmp_path / "symbols.csv"
    pd.DataFrame({"symbol": ["700.HK", "00005.XHKG", "00005.HK"]}).to_csv(
        symbols_file,
        index=False,
    )

    assert parse_symbols(symbols_file=symbols_file) == ["00700.XHKG", "00005.XHKG"]


def test_iter_dates_and_format_date() -> None:
    assert format_date("2025-03-03") == "20250303"
    assert list(iter_dates("20250303", "20250305")) == ["20250303", "20250304", "20250305"]


def test_normalize_multiindex_tick_frame() -> None:
    index = pd.MultiIndex.from_tuples(
        [("00001.XHKG", pd.Timestamp("2025-03-03 09:30:00"))],
        names=["order_book_id", "datetime"],
    )
    frame = pd.DataFrame({"last": [100.0]}, index=index)
    out = normalize_tick_frame(frame, ["last"])
    assert list(out.columns[:3]) == ["order_book_id", "datetime", "trading_date"]
    assert out.loc[0, "order_book_id"] == "00001.XHKG"
    assert out.loc[0, "trading_date"] == "20250303"
