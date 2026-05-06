from __future__ import annotations

import os
import re
from pathlib import Path

import pandas as pd
import pytest

from rqdata_tick_data.cli import main
from rqdata_tick_data.storage import atomic_write_parquet

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "command",
    [
        "probe",
        "download",
        "health",
        "aggregate-daily",
        "emit-asset",
        "quota",
        "reconcile-daily",
    ],
)
def test_cli_help(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([command, "--help"])

    assert exc.value.code == 0
    assert command in capsys.readouterr().out


def test_readme_style_offline_commands(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    daily_path = tmp_path / "daily" / "data.parquet"
    raw_asset = tmp_path / "asset_raw"
    daily_asset = tmp_path / "asset_daily"
    health_units = tmp_path / "reports" / "health_units.csv"
    daily_ref = tmp_path / "daily_ref"
    reconcile_report = tmp_path / "reports" / "reconcile.json"

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
    assert (
        main(
            [
                "health",
                "--input",
                str(raw_root),
                "--out-units",
                str(health_units),
            ]
        )
        == 0
    )
    assert main(["aggregate-daily", "--input", str(raw_root), "--output", str(daily_path)]) == 0
    assert (
        main(
            [
                "emit-asset",
                "--kind",
                "raw",
                "--source",
                str(raw_root),
                "--output",
                str(raw_asset),
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "emit-asset",
                "--kind",
                "daily",
                "--source",
                str(daily_path),
                "--output",
                str(daily_asset),
            ]
        )
        == 0
    )
    assert main(["quota", "--fake-provider", "--pretty"]) == 0

    atomic_write_parquet(
        pd.DataFrame(
            {
                "trade_date": ["20250303"],
                "symbol": ["00001.HK"],
                "open": [100.05],
                "high": [100.20],
                "low": [100.05],
                "close": [100.20],
                "volume": [10000.0],
                "total_turnover": [1001500.0],
            }
        ),
        daily_ref / "data" / "00001.HK.parquet",
    )
    assert (
        main(
            [
                "reconcile-daily",
                "--tick-input",
                str(raw_root),
                "--daily-asset-dir",
                str(daily_ref),
                "--out",
                str(reconcile_report),
                "--fail-on-severity",
                "none",
            ]
        )
        == 0
    )

    assert health_units.exists()
    assert daily_path.exists()
    assert (raw_asset / "manifest.yml").exists()
    assert (daily_asset / "manifest.yml").exists()
    assert reconcile_report.exists()


def _markdown_files() -> list[Path]:
    return [
        *sorted(REPO_ROOT.glob("*.md")),
        *sorted((REPO_ROOT / "docs").rglob("*.md")),
    ]


def test_markdown_internal_links_exist() -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    missing: list[str] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            target_path = (path.parent / target).resolve()
            if not target_path.exists():
                missing.append(f"{path.relative_to(REPO_ROOT)} -> {target}")
    assert not missing


def test_readme_and_agents_required_sections() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    inventory = (REPO_ROOT / "docs/internal/maintenance-debt-inventory.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "uv sync --group dev",
        "uv run pytest",
        "uv run ruff check .",
        "uv sync --extra rqdata --group dev",
        "FakeProvider",
        "symbol-date",
        "raw_layout=batch",
        "health",
        "reconcile-daily",
    ):
        assert required in readme or required in agents

    for item in (
        "downloader.py",
        "reconcile.py",
        "cli.py",
        "project_tools/export_repo_source.py",
        "project_tools/package.sh",
        "SchemaError",
        "cache_dataset_root",
    ):
        assert item in inventory


def test_docs_avoid_known_contrastive_phrases() -> None:
    banned = ("不是.*而是", "而非", "而不是", "本页不解决什么")
    offenders: list[str] = []
    for path in _markdown_files():
        text = path.read_text(encoding="utf-8")
        for phrase in banned:
            if re.search(phrase, text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")
    assert not offenders


@pytest.mark.rqdata_live
def test_live_rqdata_quota_smoke_opt_in() -> None:
    if os.environ.get("RQDATA_TICK_LIVE_TESTS") != "1":
        pytest.skip("Set RQDATA_TICK_LIVE_TESTS=1 to run live RQData smoke tests.")

    from rqdata_tick_data.rq_client import RQDataClient

    payload = RQDataClient().quota_snapshot()
    assert isinstance(payload, dict)
