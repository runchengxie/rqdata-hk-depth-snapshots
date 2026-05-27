"""Helpers for delegating compatibility imports to market-data-platform."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType


def ensure_platform_available() -> None:
    try:
        importlib.import_module("market_data_platform")
        return
    except ModuleNotFoundError as exc:
        if exc.name != "market_data_platform":
            raise

    workspace_root = Path(__file__).resolve().parents[3]
    platform_src = workspace_root / "market-data-platform" / "src"
    if platform_src.is_dir():
        sys.path.insert(0, str(platform_src))
        importlib.import_module("market_data_platform")
        return

    raise ModuleNotFoundError(
        "Install market-data-platform or run from a research-workspace checkout with "
        "market-data-platform/src available."
    )


def alias_platform_module(compat_name: str, platform_name: str) -> ModuleType:
    ensure_platform_available()
    module = importlib.import_module(platform_name)
    sys.modules[compat_name] = module
    return module
