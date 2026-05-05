"""RQData provider adapter."""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Protocol

import pandas as pd

from rqdata_tick_data.exceptions import ProviderRequestError


class TickDataProvider(Protocol):
    """Provider interface used by download workflows."""

    def get_price(
        self,
        order_book_ids: Sequence[str],
        start_date: str,
        end_date: str,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        """Return tick data for the requested identifiers and dates."""

    def quota_snapshot(self) -> dict[str, object] | None:
        """Return account/quota data when available."""


def classify_provider_exception(exc: BaseException) -> str:
    """Map provider exceptions into stable categories for metadata and CLI output."""
    message = str(exc).lower()
    if any(token in message for token in ("auth", "login", "password", "token", "credential")):
        return "authentication"
    if any(
        token in message
        for token in ("permission", "entitle", "unauthor", "forbidden", "no access")
    ):
        return "entitlement"
    if any(token in message for token in ("field", "invalid", "not support", "unsupported")):
        return "invalid_field"
    if any(token in message for token in ("empty", "no data", "not found")):
        return "empty_data"
    return "provider_error"


class RQDataClient:
    """Thin wrapper around `rqdatac` for HK historical tick snapshots."""

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        uri: str | None = None,
        initialize: bool = True,
    ) -> None:
        try:
            import rqdatac  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - depends on optional provider package
            raise ProviderRequestError(
                "authentication",
                "import_rqdatac",
                "rqdatac is not installed; install with `uv sync --extra rqdata`.",
            ) from exc

        self._rqdatac = rqdatac
        self.username = username or os.getenv("RQDATA_USERNAME")
        self.password = password or os.getenv("RQDATA_PASSWORD")
        self.uri = uri or os.getenv("RQDATA_URI")
        if initialize:
            self._initialize()

    def _initialize(self) -> None:
        try:
            init = self._rqdatac.init
            if self.username and self.password and self.uri:
                try:
                    init(self.uri, self.username, self.password)
                except TypeError:
                    init(username=self.username, password=self.password, address=self.uri)
            elif self.username and self.password:
                try:
                    init(username=self.username, password=self.password)
                except TypeError:
                    init(self.username, self.password)
            else:
                init()
        except Exception as exc:  # pragma: no cover - provider-specific behavior
            raise ProviderRequestError(
                classify_provider_exception(exc), "initialize_rqdata", str(exc)
            ) from exc

    def get_price(
        self,
        order_book_ids: Sequence[str],
        start_date: str,
        end_date: str,
        fields: Sequence[str],
    ) -> pd.DataFrame:
        try:
            return self._rqdatac.get_price(
                list(order_book_ids),
                start_date=start_date,
                end_date=end_date,
                frequency="tick",
                fields=list(fields),
                market="hk",
                expect_df=True,
            )
        except Exception as exc:  # pragma: no cover - provider-specific behavior
            raise ProviderRequestError(
                classify_provider_exception(exc), "get_price", str(exc)
            ) from exc

    def quota_snapshot(self) -> dict[str, object] | None:
        for name in ("get_quota", "quota", "get_account_info", "user_info"):
            attr = getattr(self._rqdatac, name, None)
            if attr is None:
                continue
            try:
                value = attr() if callable(attr) else attr
            except Exception:
                continue
            if value is None:
                continue
            if isinstance(value, dict):
                return value
            return {"value": repr(value)}
        return None
