from __future__ import annotations

from datetime import date, timedelta

from armadilha_cdi.config import MAX_USD_FALLBACK_DAYS
from armadilha_cdi.exceptions import DataUnavailableError, DomainValidationError
from armadilha_cdi.models import CalculationResult, QuoteLookup


def validate_inputs(start_date: date, end_date: date, initial_brl: float) -> None:
    if end_date <= start_date:
        raise DomainValidationError("A data final deve ser maior que a data inicial.")
    if initial_brl <= 0:
        raise DomainValidationError("O valor inicial deve ser maior que zero.")


def lookup_quote_with_fallback(
    usd_rates: dict[str, float],
    target_date: date,
    max_days_back: int = MAX_USD_FALLBACK_DAYS,
) -> QuoteLookup:
    for days_back in range(max_days_back + 1):
        candidate_date = target_date - timedelta(days=days_back)
        iso_date = candidate_date.isoformat()
        if iso_date in usd_rates:
            return QuoteLookup(
                requested_date=target_date,
                effective_date=candidate_date,
                value=usd_rates[iso_date],
            )

    raise DataUnavailableError(
        "Nao foi encontrada cotacao USD/BRL suficiente para o periodo selecionado."
    )


def calculate_cdi_factor(
    cdi_rates: dict[str, float],
    start_date: date,
    end_date: date,
) -> tuple[float, int]:
    factor = 1.0
    days_used = 0

    for iso_date in sorted(cdi_rates):
        current_date = date.fromisoformat(iso_date)
        if start_date <= current_date < end_date:
            factor *= 1 + (cdi_rates[iso_date] / 100)
            days_used += 1

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

    cdi_factor, cdi_days_used = calculate_cdi_factor(
        cdi_rates=cdi_rates,
        start_date=start_date,
        end_date=end_date,
    )
    initial_quote = lookup_quote_with_fallback(usd_rates=usd_rates, target_date=start_date)
    final_quote = lookup_quote_with_fallback(usd_rates=usd_rates, target_date=end_date)

    final_brl = initial_brl * cdi_factor
    initial_usd = initial_brl / initial_quote.value
    final_usd_with_cdi = final_brl / final_quote.value
    real_usd_return_percentage = ((final_usd_with_cdi / initial_usd) - 1) * 100

    return CalculationResult(
        start_date=start_date,
        end_date=end_date,
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
