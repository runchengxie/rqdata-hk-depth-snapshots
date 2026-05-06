from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _function_spans(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    spans: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and hasattr(node, "end_lineno"):
            spans.append((node.name, int(node.end_lineno) - int(node.lineno) + 1))
    return spans


def test_large_functions_are_listed_in_maintenance_inventory() -> None:
    inventory = (REPO_ROOT / "docs/internal/maintenance-debt-inventory.md").read_text(
        encoding="utf-8"
    )
    threshold = 160
    untracked: list[str] = []
    for path in sorted((REPO_ROOT / "src/rqdata_tick_data").glob("*.py")):
        large = [name for name, lines in _function_spans(path) if lines >= threshold]
        if large and path.name not in inventory:
            untracked.append(f"{path.relative_to(REPO_ROOT)}: {', '.join(large)}")

    assert not untracked
