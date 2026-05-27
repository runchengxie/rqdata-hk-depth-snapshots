"""Compatibility wrapper for market_data_platform.hk_depth.testing."""

from rqdata_tick_data._platform import alias_platform_module

alias_platform_module(__name__, "market_data_platform.hk_depth.testing")
