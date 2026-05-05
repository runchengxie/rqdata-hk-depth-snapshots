"""Filesystem helpers for tick-depth cache and asset outputs."""

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd


def now_stamp() -> str:
    """Return a stable UTC timestamp for filenames."""
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def cache_dataset_root(base: str | Path, dataset: str) -> Path:
    return Path(base) / dataset


def batch_part_path(dataset_root: str | Path, trade_date: str, batch_number: int) -> Path:
    return (
        Path(dataset_root)
        / "parts"
        / f"trade_date={trade_date}"
        / f"batch_{batch_number:04d}.parquet"
    )


def metadata_path(dataset_root: str | Path, kind: str, stamp: str | None = None) -> Path:
    return Path(dataset_root) / "meta" / f"{kind}_{stamp or now_stamp()}.json"


def atomic_write_parquet(df: pd.DataFrame, path: str | Path) -> Path:
    """Write parquet through a temp file and then replace the target."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        df.to_parquet(temp, index=False)
        temp.replace(target)
    finally:
        if temp.exists():
            temp.unlink()
    return target


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return repr(value)


def write_json(path: str | Path, data: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )
    return target


def write_yaml(path: str | Path, data: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml

        text = yaml.safe_dump(data, sort_keys=False, allow_unicode=False)
    except Exception:
        text = json.dumps(data, indent=2, sort_keys=False, default=_json_default)
    target.write_text(text, encoding="utf-8")
    return target


def discover_parquet_parts(path: str | Path) -> list[Path]:
    """Find parquet files under a raw cache, asset, directory, or single file."""
    root = Path(path)
    if root.is_file() and root.suffix == ".parquet":
        return [root]
    if not root.exists():
        return []
    search_root = root / "parts" if (root / "parts").exists() else root
    return sorted(
        part
        for part in search_root.rglob("*.parquet")
        if ".tmp" not in part.name and not part.name.startswith(".")
    )


def load_parquet_parts(path: str | Path) -> pd.DataFrame:
    parts = discover_parquet_parts(path)
    if not parts:
        return pd.DataFrame()
    return pd.concat((pd.read_parquet(part) for part in parts), ignore_index=True)


def copy_parquet_tree(source_root: str | Path, output_data_root: str | Path) -> list[Path]:
    """Copy parquet parts while preserving partition-like relative paths."""
    source = Path(source_root)
    output = Path(output_data_root)
    copied: list[Path] = []
    parts_base = source / "parts"
    for part in discover_parquet_parts(source):
        try:
            rel = part.relative_to(parts_base)
        except ValueError:
            rel = part.name if part.is_file() else part.relative_to(source)
        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(part, target)
        copied.append(target)
    return copied
