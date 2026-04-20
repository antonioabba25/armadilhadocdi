from __future__ import annotations

from datetime import date, datetime, timedelta

import requests

from armadilha_cdi.config import (
    BCB_HEADERS,
    CDI_SERIES_URL,
    DATE_DISPLAY_FORMAT,
    DATE_STORAGE_FORMAT,
    MAX_USD_FALLBACK_DAYS,
    PTAX_QUERY_FORMAT,
    PTAX_URL_TEMPLATE,
    REQUEST_TIMEOUT_SECONDS,
)
from armadilha_cdi.exceptions import MarketDataError
from armadilha_cdi.models import MarketDataBundle
from armadilha_cdi.services.cache import JsonFileCache


class BCBMarketDataProvider:
    """Fetches and caches CDI and USD/BRL data from Banco Central."""

    def __init__(
        self,
        cache_repository: JsonFileCache,
        timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.cache_repository = cache_repository
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update(BCB_HEADERS)

    def get_market_data(self, start_date: date, end_date: date) -> MarketDataBundle:
        """Return cached + synchronized market data for the requested window."""
        if end_date <= start_date:
            raise MarketDataError("A data final deve ser maior que a data inicial.")

        cdi_rates = self._ensure_cdi_data(start_date=start_date, end_date=end_date)
        usd_rates = self._ensure_usd_data(
            start_date=start_date - timedelta(days=MAX_USD_FALLBACK_DAYS),
            end_date=end_date,
        )
        return MarketDataBundle(cdi_rates=cdi_rates, usd_rates=usd_rates)

    def _ensure_cdi_data(self, start_date: date, end_date: date) -> dict[str, float]:
        cached = self.cache_repository.load("cdi.json")
        if self._covers_window(cached, start_date, end_date, tolerance_days=3):
            return cached

        fresh = self._fetch_cdi_rates(start_date=start_date, end_date=end_date)
        if not fresh and not cached:
            raise MarketDataError("Nao foi possivel obter os dados de CDI do Banco Central.")

        return self.cache_repository.merge("cdi.json", fresh)

    def _ensure_usd_data(self, start_date: date, end_date: date) -> dict[str, float]:
        cached = self.cache_repository.load("usd.json")
        if self._covers_window(
            cached,
            start_date,
            end_date,
            tolerance_days=MAX_USD_FALLBACK_DAYS,
        ):
            return cached

        fresh = self._fetch_usd_rates(start_date=start_date, end_date=end_date)
        if not fresh and not cached:
            raise MarketDataError("Nao foi possivel obter as cotacoes USD/BRL do Banco Central.")

        return self.cache_repository.merge("usd.json", fresh)

    @staticmethod
    def _covers_window(
        series: dict[str, float],
        start_date: date,
        end_date: date,
        tolerance_days: int,
    ) -> bool:
        if not series:
            return False

        ordered_keys = sorted(series)
        min_cached = date.fromisoformat(ordered_keys[0])
        max_cached = date.fromisoformat(ordered_keys[-1])
        return (
            min_cached <= start_date
            and max_cached >= (end_date - timedelta(days=tolerance_days))
        )

    def _fetch_cdi_rates(self, start_date: date, end_date: date) -> dict[str, float]:
        params = {
            "formato": "json",
            "dataInicial": start_date.strftime(DATE_DISPLAY_FORMAT),
            "dataFinal": end_date.strftime(DATE_DISPLAY_FORMAT),
        }

        try:
            response = self.session.get(
                CDI_SERIES_URL,
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise MarketDataError(f"Falha ao consultar CDI no Banco Central: {exc}") from exc
        except ValueError as exc:
            raise MarketDataError("Resposta invalida ao consultar o CDI.") from exc

        parsed: dict[str, float] = {}
        for item in payload:
            try:
                parsed_date = datetime.strptime(item["data"], DATE_DISPLAY_FORMAT).date()
            except (KeyError, TypeError, ValueError):
                continue

            try:
                parsed[parsed_date.strftime(DATE_STORAGE_FORMAT)] = float(item["valor"])
            except (KeyError, TypeError, ValueError):
                continue
        return parsed

    def _fetch_usd_rates(self, start_date: date, end_date: date) -> dict[str, float]:
        url = PTAX_URL_TEMPLATE.format(
            start=start_date.strftime(PTAX_QUERY_FORMAT),
            end=end_date.strftime(PTAX_QUERY_FORMAT),
        )
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            raise MarketDataError(f"Falha ao consultar PTAX no Banco Central: {exc}") from exc
        except ValueError as exc:
            raise MarketDataError("Resposta invalida ao consultar a PTAX.") from exc

        parsed: dict[str, float] = {}
        for item in payload.get("value", []):
            try:
                iso_date = item["dataHoraCotacao"].split(" ")[0]
                parsed[iso_date] = float(item["cotacaoVenda"])
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
        return parsed
