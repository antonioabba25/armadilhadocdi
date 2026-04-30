from __future__ import annotations

from bisect import bisect_right
from datetime import date

from armadilha_cdi.config import (
    EARLIEST_SUPPORTED_DATE,
    MAX_MARKET_DATE_FALLBACK_DAYS,
    MAX_USD_FALLBACK_DAYS,
)
from armadilha_cdi.exceptions import DataUnavailableError, DomainValidationError
from armadilha_cdi.models import CalculationResult, QuoteLookup


def validate_inputs(start_date: date, end_date: date, initial_brl: float) -> None:
    if start_date < EARLIEST_SUPPORTED_DATE:
        raise DomainValidationError(
            "A data inicial deve ser em ou posterior a "
            f"{EARLIEST_SUPPORTED_DATE.strftime('%d/%m/%Y')}, "
            "quando o real brasileiro entrou em circulacao."
        )
    if end_date <= start_date:
        raise DomainValidationError("A data final deve ser maior que a data inicial.")
    if initial_brl <= 0:
        raise DomainValidationError("O valor inicial deve ser maior que zero.")


class QuoteResolver:
    """Resolve USD/BRL quotes using the nearest previous available date."""

    def __init__(
        self,
        usd_rates: dict[str, float],
        max_days_back: int = MAX_USD_FALLBACK_DAYS,
        min_date: date | None = None,
    ) -> None:
        self.max_days_back = max_days_back
        self.min_date = min_date
        self._values_by_date: dict[date, float] = {}

        for iso_date, value in usd_rates.items():
            try:
                parsed_date = date.fromisoformat(iso_date)
                if self.min_date is not None and parsed_date < self.min_date:
                    continue
                self._values_by_date[parsed_date] = float(value)
            except (TypeError, ValueError):
                continue

        self._ordered_dates = sorted(self._values_by_date)

    def lookup(self, target_date: date) -> QuoteLookup:
        index = bisect_right(self._ordered_dates, target_date) - 1
        if index >= 0:
            effective_date = self._ordered_dates[index]
            if (target_date - effective_date).days <= self.max_days_back:
                return QuoteLookup(
                    requested_date=target_date,
                    effective_date=effective_date,
                    value=self._values_by_date[effective_date],
                )

        raise DataUnavailableError(
            "Nao foi encontrada cotacao USD/BRL suficiente para o periodo selecionado."
        )


class MarketDateResolver:
    """Resolve official market dates using the nearest previous available date."""

    def __init__(
        self,
        series: dict[str, float],
        label: str,
        max_days_back: int = MAX_MARKET_DATE_FALLBACK_DAYS,
        min_date: date | None = None,
    ) -> None:
        self.label = label
        self.max_days_back = max_days_back
        self.min_date = min_date
        self._ordered_dates: list[date] = []

        for iso_date in series:
            try:
                parsed_date = date.fromisoformat(str(iso_date))
                if self.min_date is not None and parsed_date < self.min_date:
                    continue
                self._ordered_dates.append(parsed_date)
            except (TypeError, ValueError):
                continue

        self._ordered_dates = sorted(set(self._ordered_dates))

    def lookup(
        self,
        target_date: date,
        allow_forward_if_before_first: bool = False,
    ) -> date:
        index = bisect_right(self._ordered_dates, target_date) - 1
        if index >= 0:
            effective_date = self._ordered_dates[index]
            if (target_date - effective_date).days <= self.max_days_back:
                return effective_date

        if allow_forward_if_before_first and self._ordered_dates:
            effective_date = self._ordered_dates[0]
            if (
                target_date <= effective_date
                and (effective_date - target_date).days <= self.max_days_back
            ):
                return effective_date

        raise DataUnavailableError(
            f"Nao foi encontrado dado de {self.label} suficiente para o periodo selecionado."
        )


def lookup_quote_with_fallback(
    usd_rates: dict[str, float],
    target_date: date,
    max_days_back: int = MAX_USD_FALLBACK_DAYS,
) -> QuoteLookup:
    return QuoteResolver(usd_rates=usd_rates, max_days_back=max_days_back).lookup(target_date)


def resolve_cdi_period(
    cdi_rates: dict[str, float],
    start_date: date,
    end_date: date,
) -> tuple[date, date]:
    resolver = MarketDateResolver(
        series=cdi_rates,
        label="CDI",
        min_date=EARLIEST_SUPPORTED_DATE,
    )
    effective_start_date = resolver.lookup(
        start_date,
        allow_forward_if_before_first=True,
    )
    effective_end_date = resolver.lookup(end_date)

    if effective_end_date <= effective_start_date:
        raise DataUnavailableError("Nao ha dias uteis de CDI suficientes para o periodo informado.")

    return effective_start_date, effective_end_date


def calculate_cdi_factor(
    cdi_rates: dict[str, float],
    start_date: date,
    end_date: date,
) -> tuple[float, int]:
    factor = 1.0
    start_key = start_date.isoformat()
    end_key = end_date.isoformat()

    window_rates: list[tuple[str, float]] = []
    for iso_date, rate in cdi_rates.items():
        if not isinstance(iso_date, str):
            continue
        if start_key <= iso_date < end_key:
            try:
                date.fromisoformat(iso_date)
                window_rates.append((iso_date, float(rate)))
            except (TypeError, ValueError):
                continue

    for _, rate in sorted(window_rates):
        factor *= 1 + (rate / 100)

    days_used = len(window_rates)

    if days_used == 0:
        raise DataUnavailableError("Nao ha dados de CDI suficientes para o periodo informado.")

    return factor, days_used


def calculate_result(
    start_date: date,
    end_date: date,
    initial_brl: float,
    cdi_rates: dict[str, float],
    usd_rates: dict[str, float],
) -> CalculationResult:
    validate_inputs(start_date=start_date, end_date=end_date, initial_brl=initial_brl)
    effective_start_date, effective_end_date = resolve_cdi_period(
        cdi_rates=cdi_rates,
        start_date=start_date,
        end_date=end_date,
    )

    cdi_factor, cdi_days_used = calculate_cdi_factor(
        cdi_rates=cdi_rates,
        start_date=effective_start_date,
        end_date=effective_end_date,
    )
    quote_resolver = QuoteResolver(usd_rates=usd_rates, min_date=EARLIEST_SUPPORTED_DATE)
    initial_quote = quote_resolver.lookup(effective_start_date)
    final_quote = quote_resolver.lookup(effective_end_date)

    final_brl = initial_brl * cdi_factor
    initial_usd = initial_brl / initial_quote.value
    final_usd_with_cdi = final_brl / final_quote.value
    real_usd_return_percentage = ((final_usd_with_cdi / initial_usd) - 1) * 100

    return CalculationResult(
        start_date=start_date,
        end_date=end_date,
        effective_start_date=effective_start_date,
        effective_end_date=effective_end_date,
        initial_brl=initial_brl,
        final_brl=final_brl,
        cdi_factor=cdi_factor,
        cdi_percentage=(cdi_factor - 1) * 100,
        initial_usd=initial_usd,
        final_usd_with_cdi=final_usd_with_cdi,
        initial_usdbrl=initial_quote.value,
        final_usdbrl=final_quote.value,
        initial_fx_date=initial_quote.effective_date,
        final_fx_date=final_quote.effective_date,
        real_usd_return_percentage=real_usd_return_percentage,
        cdi_days_used=cdi_days_used,
    )
