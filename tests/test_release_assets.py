from __future__ import annotations

import tarfile
from pathlib import Path

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
