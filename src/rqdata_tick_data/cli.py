"""Compatibility wrapper for market_data_platform.hk_depth.cli."""

from rqdata_tick_data._platform import alias_platform_module

_module = alias_platform_module(__name__, "market_data_platform.hk_depth.cli")

if __name__ == "__main__":
    _module.main_entry()
