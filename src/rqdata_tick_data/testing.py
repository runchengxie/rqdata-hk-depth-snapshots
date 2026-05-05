"""Offline fake provider used by tests and dry local demonstrations."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


class FakeProvider:
    """Deterministic tick provider that mimics RQData's indexed dataframe shape."""

    def get_price(
        self,
        order_book_ids: Sequence[str],
        start_date: str,
        end_date: str,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        rows = []
        index = []
        timestamps = pd.date_range(
            f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} 09:30:00",
            periods=4,
            freq="10min",
        )
        for symbol_index, symbol in enumerate(order_book_ids):
            base = 100.0 + symbol_index
            cumulative_volume = 0
            cumulative_turnover = 0.0
            for tick_index, timestamp in enumerate(timestamps, start=1):
                last = base + tick_index * 0.05
                cumulative_volume += 1000 * tick_index
                cumulative_turnover += last * 1000 * tick_index
                row = {"trading_date": start_date}
                for field in fields:
                    if field == "last":
                        row[field] = last
                    elif field == "volume":
                        row[field] = cumulative_volume
                    elif field == "total_turnover":
                        row[field] = cumulative_turnover
                    elif field == "prev_close":
                        row[field] = base - 0.25
                    elif field.startswith("a") and field.endswith("_v"):
                        level = int(field[1:-2])
                        row[field] = 1000 + level * 10
                    elif field.startswith("b") and field.endswith("_v"):
                        level = int(field[1:-2])
                        row[field] = 900 + level * 10
                    elif field.startswith("a") and field[1:].isdigit():
                        level = int(field[1:])
                        row[field] = last + level * 0.01
                    elif field.startswith("b") and field[1:].isdigit():
                        level = int(field[1:])
                        row[field] = last - level * 0.01
                    else:
                        row[field] = pd.NA
                rows.append(row)
                index.append((symbol, timestamp))
        frame = pd.DataFrame(rows)
        frame.index = pd.MultiIndex.from_tuples(index, names=["order_book_id", "datetime"])
        return frame

    def quota_snapshot(self) -> dict[str, object]:
        return {"fake": True}
