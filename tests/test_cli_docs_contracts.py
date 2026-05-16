from __future__ import annotations

import argparse
import ast
import os
import re
from pathlib import Path

import pandas as pd
import pytest
import yaml

from rqdata_tick_data.cli import build_parser, main
from rqdata_tick_data.storage import atomic_write_parquet

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "command",
    [
        "probe",
        "download",
        "health",
        "aggregate-daily",
        "recompress-raw",
        "emit-asset",
        "package-assets",
        "release-assets",
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


def _project_authored_markdown_files() -> list[Path]:
    return [
        path
        for path in _markdown_files()
        if "docs/vendor" not in path.relative_to(REPO_ROOT).as_posix()
    ]


def _stable_markdown_files() -> list[Path]:
    return [
        path
        for path in _project_authored_markdown_files()
        if "docs/records" not in path.relative_to(REPO_ROOT).as_posix()
    ]


def _parser_commands() -> dict[str, set[str]]:
    parser = build_parser()
    commands: dict[str, set[str]] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for command, subparser in action.choices.items():
                options: set[str] = set()
                for sub_action in subparser._actions:
                    options.update(
                        option
                        for option in sub_action.option_strings
                        if option.startswith("--")
                    )
                commands[command] = options
    return commands


def _rqdata_client_env_vars() -> set[str]:
    path = REPO_ROOT / "src/rqdata_tick_data/rq_client.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "getenv"
            and isinstance(func.value, ast.Name)
            and func.value.id == "os"
        ):
            continue
        if not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            if arg.value.startswith("RQDATA_"):
                names.add(arg.value)
    return names


def _manifest_file_nodes(node):  # noqa: ANN001
    if isinstance(node, dict):
        if "file" in node:
            yield node
        for value in node.values():
            yield from _manifest_file_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _manifest_file_nodes(value)


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


def test_cli_docs_cover_parser_commands_and_options() -> None:
    docs = (REPO_ROOT / "docs/cli.md").read_text(encoding="utf-8")
    missing: list[str] = []
    for command, options in _parser_commands().items():
        if command not in docs:
            missing.append(command)
        for option in sorted(options):
            if option not in docs:
                missing.append(f"{command}: {option}")
    assert not missing


def test_rqdata_env_vars_are_documented_without_sample_credentials() -> None:
    expected = _rqdata_client_env_vars()
    documented = "\n".join(
        [
            (REPO_ROOT / "docs/providers-rqdata.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs/development.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
        ]
    )
    missing_from_docs = sorted(name for name in expected if name not in documented)

    assert not (REPO_ROOT / ".env.example").exists()
    assert ".env.example" not in documented
    assert not missing_from_docs


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


def test_docs_avoid_known_contrastive_or_negating_phrases() -> None:
    banned = (
        "不是",
        "而是",
        "而非",
        "而不是",
        "本页不解决什么",
        "不作为.*而",
        "不直接.*而",
        "什麽",
        "什麼",
    )
    offenders: list[str] = []
    for path in _project_authored_markdown_files():
        text = path.read_text(encoding="utf-8")
        for phrase in banned:
            if re.search(phrase, text):
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")
    assert not offenders


def test_stable_docs_do_not_contain_local_or_dated_record_facts() -> None:
    banned = ("/home/", "TRIAL", "1GB/day", "当前账号", "当前 add-on", "历史 tick 权限从")
    offenders: list[str] = []
    for path in _stable_markdown_files():
        text = path.read_text(encoding="utf-8")
        for phrase in banned:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")
    assert not offenders


def test_records_index_lists_all_dated_records() -> None:
    records_dir = REPO_ROOT / "docs/records"
    index = (records_dir / "README.md").read_text(encoding="utf-8")
    missing = [
        path.name
        for path in sorted(records_dir.glob("*.md"))
        if path.name != "README.md" and path.name not in index
    ]
    assert not missing


def test_records_are_dated_and_mark_record_context() -> None:
    offenders: list[str] = []
    records_dir = REPO_ROOT / "docs/records"
    for path in sorted(records_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        heading = text.splitlines()[0] if text.splitlines() else ""
        has_date = re.search(r"\d{4}-\d{2}-\d{2}", path.name) or re.search(
            r"\d{4}-\d{2}-\d{2}", heading
        )
        if not has_date:
            offenders.append(f"{path.relative_to(REPO_ROOT)}: missing date")
        if not re.search(r"记录日期|Status date", text):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: missing record date context")
        if "/home/" in text and not re.search(r"本地|record-specific|记录", text):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: local path lacks record context")
    assert not offenders


def test_stable_docs_do_not_depend_on_local_configs() -> None:
    offenders: list[str] = []
    for path in _stable_markdown_files():
        text = path.read_text(encoding="utf-8")
        if "configs/" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders


def test_universe_manifest_references_existing_files_and_symbol_counts() -> None:
    universe_root = REPO_ROOT / "configs/universe/hk_tick_depth"
    manifest = yaml.safe_load((universe_root / "manifest.yml").read_text(encoding="utf-8"))
    nodes = list(_manifest_file_nodes(manifest))
    listed = {str(node["file"]) for node in nodes}
    expected_txt = {
        path.relative_to(universe_root).as_posix() for path in universe_root.rglob("*.txt")
    }
    errors: list[str] = []

    for node in nodes:
        rel_path = str(node["file"])
        path = universe_root / rel_path
        if not path.exists():
            errors.append(f"missing manifest file: {rel_path}")
            continue
        if path.suffix == ".txt" and "symbols" in node:
            symbols = [
                line.strip()
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            if len(symbols) != int(node["symbols"]):
                errors.append(
                    f"{rel_path}: manifest symbols={node['symbols']} actual={len(symbols)}"
                )

    missing_from_manifest = sorted(expected_txt - listed)
    errors.extend(f"unlisted symbol list: {path}" for path in missing_from_manifest)
    assert not errors


@pytest.mark.rqdata_live
def test_live_rqdata_quota_smoke_opt_in() -> None:
    if os.environ.get("RQDATA_TICK_LIVE_TESTS") != "1":
        pytest.skip("Set RQDATA_TICK_LIVE_TESTS=1 to run live RQData smoke tests.")

    from rqdata_tick_data.rq_client import RQDataClient

    payload = RQDataClient().quota_snapshot()
    assert isinstance(payload, dict)
