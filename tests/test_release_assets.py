from __future__ import annotations

import io
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

from rqdata_tick_data.cli import main
from rqdata_tick_data.release_assets import package_tick_assets


def _write(path: Path, text: str = "data") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_package_tick_assets_writes_manifest_readme_and_tarballs(tmp_path: Path) -> None:
    raw = tmp_path / "asset_raw"
    daily = tmp_path / "asset_daily"
    record = tmp_path / "docs" / "records" / "record.md"
    config = tmp_path / "configs" / "universe" / "symbols.txt"
    _write(raw / "manifest.yml", "schema_version: tick_depth_raw.v1\n")
    _write(raw / "data" / "part.parquet", "raw")
    _write(daily / "manifest.yml", "schema_version: tick_depth_daily.v1\n")
    _write(daily / "data" / "data.parquet", "daily")
    _write(record, "# record\n")
    _write(config, "00001.XHKG\n")

    tar_dir = tmp_path / "tarballs"
    payload = package_tick_assets(
        repo_root=tmp_path,
        name="demo",
        as_of="20250102",
        tar_dir=tar_dir,
        raw_sources=[str(raw)],
        daily_sources=[str(daily)],
        metadata_sources=[str(record)],
        config_sources=[str(config)],
        parts=["raw", "daily", "metadata", "configs"],
    )

    assert (tar_dir / "manifest.yml").exists()
    assert (tar_dir / "manifest.json").exists()
    assert (tar_dir / "README.md").exists()
    assert {item["part"] for item in payload["tarballs"]} == {
        "raw",
        "daily",
        "metadata",
        "configs",
    }

    raw_tar = tar_dir / "demo-20250102-raw-part001.tar.gz"
    assert raw_tar.exists()
    with tarfile.open(raw_tar, "r:gz") as tar:
        names = set(tar.getnames())
    assert "raw/asset_raw/manifest.yml" in names
    assert "raw/asset_raw/data/part.parquet" in names


def test_package_tick_assets_writes_tar_zst_when_requested(tmp_path: Path) -> None:
    if shutil.which("zstd") is None:
        pytest.skip("zstd binary is not available")

    raw = tmp_path / "raw"
    _write(raw / "manifest.yml", "schema_version: tick_depth_raw.v1\n")
    _write(raw / "data" / "part.parquet", "raw")
    tar_dir = tmp_path / "tarballs"

    payload = package_tick_assets(
        repo_root=tmp_path,
        name="cold",
        as_of="20250104",
        tar_dir=tar_dir,
        raw_sources=[str(raw)],
        parts=["raw"],
        archive_format="tar.zst",
        archive_compression_level=12,
    )

    raw_tar = tar_dir / "cold-20250104-raw-part001.tar.zst"
    assert raw_tar.exists()
    assert payload["distribution"]["archive_format"] == "tar.zst"
    assert payload["distribution"]["archive_compression_level"] == 12

    result = subprocess.run(
        ["zstd", "-dc", str(raw_tar)],
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as tar:
        names = set(tar.getnames())
    assert "raw/raw/manifest.yml" in names
    assert "raw/raw/data/part.parquet" in names


def test_package_tick_assets_can_dedupe_symbol_date_raw_parts(tmp_path: Path) -> None:
    old_raw = tmp_path / "old_raw"
    new_raw = tmp_path / "new_raw"
    duplicate = Path("parts/trade_date=20250102/order_book_id=00001.XHKG.parquet")
    old_duplicate = _write(old_raw / duplicate, "old")
    new_duplicate = _write(new_raw / duplicate, "new")
    unique = _write(
        old_raw / "parts/trade_date=20250102/order_book_id=00002.XHKG.parquet",
        "u",
    )
    _write(old_raw / "manifest.yml", "old\n")
    _write(new_raw / "manifest.yml", "new\n")
    os.utime(old_duplicate, (1, 1))
    os.utime(new_duplicate, (2, 2))
    os.utime(unique, (1, 1))

    tar_dir = tmp_path / "tarballs"
    payload = package_tick_assets(
        repo_root=tmp_path,
        name="dedupe",
        as_of="20250105",
        tar_dir=tar_dir,
        raw_sources=[str(old_raw), str(new_raw)],
        parts=["raw"],
        raw_dedupe="symbol-date",
    )

    assert payload["dedupe"]["raw"]["dropped_entries"] == 1
    raw_tar = tar_dir / "dedupe-20250105-raw-part001.tar.gz"
    with tarfile.open(raw_tar, "r:gz") as tar:
        names = set(tar.getnames())
    duplicate_names = [name for name in names if name.endswith(duplicate.as_posix())]
    assert duplicate_names == [
        "raw/new_raw/parts/trade_date=20250102/order_book_id=00001.XHKG.parquet"
    ]
    assert (
        "raw/old_raw/parts/trade_date=20250102/order_book_id=00002.XHKG.parquet"
        in names
    )


def test_package_assets_cli_and_release_assets_dry_run(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _write(raw / "manifest.yml", "schema_version: tick_depth_raw.v1\n")
    _write(raw / "data" / "part.parquet", "raw")
    tar_dir = tmp_path / "tarballs"

    assert (
        main(
            [
                "package-assets",
                "--name",
                "cli-demo",
                "--as-of",
                "20250103",
                "--tar-dir",
                str(tar_dir),
                "--raw-source",
                str(raw),
                "--part",
                "raw",
            ]
        )
        == 0
    )
    assert (tar_dir / "cli-demo-20250103-raw-part001.tar.gz").exists()

    assert (
        main(
            [
                "release-assets",
                "--tar-dir",
                str(tar_dir),
                "--tag",
                "tick-depth-test",
                "--dry-run",
            ]
        )
        == 0
    )


def test_package_assets_cli_tar_zst_and_release_assets_dry_run(tmp_path: Path) -> None:
    if shutil.which("zstd") is None:
        pytest.skip("zstd binary is not available")

    raw = tmp_path / "raw"
    _write(
        raw / "parts" / "trade_date=20250103" / "order_book_id=00001.XHKG.parquet",
        "raw",
    )
    tar_dir = tmp_path / "tarballs"

    assert (
        main(
            [
                "package-assets",
                "--name",
                "cli-cold",
                "--as-of",
                "20250106",
                "--tar-dir",
                str(tar_dir),
                "--raw-source",
                str(raw),
                "--part",
                "raw",
                "--archive-format",
                "tar.zst",
                "--archive-compression-level",
                "12",
                "--raw-dedupe",
                "symbol-date",
            ]
        )
        == 0
    )
    assert (tar_dir / "cli-cold-20250106-raw-part001.tar.zst").exists()

    assert (
        main(
            [
                "release-assets",
                "--tar-dir",
                str(tar_dir),
                "--tag",
                "tick-depth-test",
                "--dry-run",
            ]
        )
        == 0
    )
