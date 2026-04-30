from __future__ import annotations

from datetime import date, datetime, timedelta
from time import sleep
from typing import Callable

import requests

from armadilha_cdi.config import (
    BCB_HEADERS,
    CDI_QUERY_CHUNK_DAYS,
    CDI_QUERY_CHUNK_DELAY_SECONDS,
    CDI_SERIES_URL,
    DATE_DISPLAY_FORMAT,
    DATE_STORAGE_FORMAT,
    EARLIEST_SUPPORTED_DATE,
    MAX_MARKET_DATE_FALLBACK_DAYS,
    MAX_USD_FALLBACK_DAYS,
    PTAX_QUERY_FORMAT,
    PTAX_URL_TEMPLATE,
    REQUEST_TIMEOUT_SECONDS,
)
from armadilha_cdi.exceptions import MarketDataError
from armadilha_cdi.models import MarketDataBundle
from armadilha_cdi.services.cache import TimeSeriesCache


class BCBMarketDataProvider:
    """Fetches and caches CDI and USD/BRL data from Banco Central."""

    def __init__(
        self,
        cache_repository: TimeSeriesCache,
        timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
        cdi_chunk_days: int = CDI_QUERY_CHUNK_DAYS,
        cdi_chunk_delay_seconds: float = CDI_QUERY_CHUNK_DELAY_SECONDS,
        sleep_func: Callable[[float], None] = sleep,
    ) -> None:
        self.cache_repository = cache_repository
        self.timeout_seconds = timeout_seconds
        self.cdi_chunk_days = max(1, cdi_chunk_days)
        self.cdi_chunk_delay_seconds = max(0.0, cdi_chunk_delay_seconds)
        self.sleep_func = sleep_func

    def get_market_data(self, start_date: date, end_date: date) -> MarketDataBundle:
        """Return cached + synchronized market data for the requested window."""
        if start_date < EARLIEST_SUPPORTED_DATE:
            raise MarketDataError(
                "A data inicial deve ser em ou posterior a "
                f"{EARLIEST_SUPPORTED_DATE.strftime('%d/%m/%Y')}, "
                "quando o real brasileiro entrou em circulacao."
            )
        if end_date <= start_date:
            raise MarketDataError("A data final deve ser maior que a data inicial.")

        cdi_rates = self._ensure_cdi_data(
            start_date=max(
                EARLIEST_SUPPORTED_DATE,
                start_date - timedelta(days=MAX_MARKET_DATE_FALLBACK_DAYS),
            ),
            end_date=end_date,
        )
        usd_rates = self._ensure_usd_data(
            start_date=max(
                EARLIEST_SUPPORTED_DATE,
                start_date - timedelta(days=MAX_USD_FALLBACK_DAYS),
            ),
            end_date=end_date,
        )
        return MarketDataBundle(cdi_rates=cdi_rates, usd_rates=usd_rates)

    def _ensure_cdi_data(self, start_date: date, end_date: date) -> dict[str, float]:
        cached = self.cache_repository.load("cdi.json")
        if self._covers_window(cached, start_date, end_date, tolerance_days=3):
            return cached

        fresh: dict[str, float] = {}
        for fetch_start, fetch_end in self._missing_fetch_windows(
            cached=cached,
            start_date=start_date,
            end_date=end_date,
            tolerance_days=3,
        ):
            fresh.update(
                self._fetch_cdi_rates(start_date=fetch_start, end_date=fetch_end)
            )

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

        fresh: dict[str, float] = {}
        for fetch_start, fetch_end in self._missing_fetch_windows(
            cached=cached,
            start_date=start_date,
            end_date=end_date,
            tolerance_days=MAX_USD_FALLBACK_DAYS,
        ):
            fresh.update(
                self._fetch_usd_rates(start_date=fetch_start, end_date=fetch_end)
            )

        if not fresh and not cached:
            raise MarketDataError("Nao foi possivel obter as cotacoes USD/BRL do Banco Central.")

        return self.cache_repository.merge("usd.json", fresh)

    @classmethod
    def _missing_fetch_windows(
        cls,
        cached: dict[str, float],
        start_date: date,
        end_date: date,
        tolerance_days: int,
    ) -> list[tuple[date, date]]:
        bounds = cls._cached_bounds(cached)
        if bounds is None:
            return [(start_date, end_date)]

        min_cached, max_cached = bounds
        windows: list[tuple[date, date]] = []

        if min_cached > start_date:
            window_end = min(min_cached - timedelta(days=1), end_date)
            windows.append((start_date, window_end))

        if max_cached < end_date - timedelta(days=tolerance_days):
            window_start = max(max_cached + timedelta(days=1), start_date)
            windows.append((window_start, end_date))

        return [
            (window_start, window_end)
            for window_start, window_end in windows
            if window_start <= window_end
        ]

    @staticmethod
    def _cached_bounds(series: dict[str, float]) -> tuple[date, date] | None:
        if not series:
            return None

        min_cached: date | None = None
        max_cached: date | None = None
        for iso_date in series:
            try:
                parsed_date = date.fromisoformat(iso_date)
            except (TypeError, ValueError):
                continue

            if min_cached is None or parsed_date < min_cached:
                min_cached = parsed_date
            if max_cached is None or parsed_date > max_cached:
                max_cached = parsed_date

        if min_cached is None or max_cached is None:
            return None

        return min_cached, max_cached

    @classmethod
    def _covers_window(
        cls,
        series: dict[str, float],
        start_date: date,
        end_date: date,
        tolerance_days: int,
    ) -> bool:
        bounds = cls._cached_bounds(series)
        if bounds is None:
            return False

        min_cached, max_cached = bounds
        return (
            min_cached <= start_date
            and max_cached >= (end_date - timedelta(days=tolerance_days))
        )

    def _fetch_cdi_rates(self, start_date: date, end_date: date) -> dict[str, float]:
        chunks = list(self._iter_date_chunks(start_date, end_date, self.cdi_chunk_days))
        parsed: dict[str, float] = {}

        for index, (chunk_start, chunk_end) in enumerate(chunks):
            parsed.update(
                self._fetch_cdi_rates_chunk(start_date=chunk_start, end_date=chunk_end)
            )
            if index < len(chunks) - 1 and self.cdi_chunk_delay_seconds > 0:
                self.sleep_func(self.cdi_chunk_delay_seconds)

        return parsed

    @staticmethod
    def _iter_date_chunks(
        start_date: date,
        end_date: date,
        chunk_days: int,
    ) -> list[tuple[date, date]]:
        if end_date < start_date:
            return []

        chunks: list[tuple[date, date]] = []
        chunk_start = start_date
        safe_chunk_days = max(1, chunk_days)
        while chunk_start <= end_date:
            chunk_end = min(
                chunk_start + timedelta(days=safe_chunk_days - 1),
                end_date,
            )
            chunks.append((chunk_start, chunk_end))
            chunk_start = chunk_end + timedelta(days=1)
        return chunks

    def _fetch_cdi_rates_chunk(self, start_date: date, end_date: date) -> dict[str, float]:
        params = {
            "formato": "json",
            "dataInicial": start_date.strftime(DATE_DISPLAY_FORMAT),
            "dataFinal": end_date.strftime(DATE_DISPLAY_FORMAT),
        }

        try:
            response = requests.get(
                CDI_SERIES_URL,
                params=params,
                headers=BCB_HEADERS,
                timeout=self.timeout_seconds,
            )
            if response.status_code >= 400:
                detail = self._response_error_detail(response)
                if detail:
                    raise MarketDataError(
                        f"Falha ao consultar CDI no Banco Central: {detail}"
                    )
                response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            detail = self._response_error_detail(getattr(exc, "response", None))
            message = detail or str(exc)
            raise MarketDataError(f"Falha ao consultar CDI no Banco Central: {message}") from exc
        except ValueError as exc:
            detail = self._response_error_detail(response)
            message = f"Resposta invalida ao consultar o CDI: {detail}" if detail else (
                "Resposta invalida ao consultar o CDI."
            )
            raise MarketDataError(message) from exc

        if not isinstance(payload, list):
            detail = self._payload_error_detail(payload)
            message = f"Resposta invalida ao consultar o CDI: {detail}" if detail else (
                "Resposta invalida ao consultar o CDI."
            )
            raise MarketDataError(message)

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

    @classmethod
    def _response_error_detail(cls, response: requests.Response | None) -> str:
        if response is None:
            return ""

        try:
            payload = response.json()
        except ValueError:
            text = response.text.strip()
            if not text:
                return ""
            if "Requisi" in text and "inv" in text:
                return "BCB retornou uma pagina HTML de requisicao invalida."
            return text[:200]

        return cls._payload_error_detail(payload)

    @staticmethod
    def _payload_error_detail(payload: object) -> str:
        if not isinstance(payload, dict):
            return ""

        for key in ("message", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _fetch_usd_rates(self, start_date: date, end_date: date) -> dict[str, float]:
        url = PTAX_URL_TEMPLATE.format(
            start=start_date.strftime(PTAX_QUERY_FORMAT),
            end=end_date.strftime(PTAX_QUERY_FORMAT),
        )
        try:
            response = requests.get(
                url,
                headers=BCB_HEADERS,
                timeout=self.timeout_seconds,
            )
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
