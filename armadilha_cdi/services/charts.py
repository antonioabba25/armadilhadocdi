from __future__ import annotations

from datetime import date

import pandas as pd

from armadilha_cdi.services.calculations import (
    QuoteResolver,
    resolve_cdi_period,
    validate_inputs,
)


def _valid_cdi_dates(cdi_rates: dict[str, float]) -> list[date]:
    parsed_dates: list[date] = []
    for iso_date in cdi_rates:
        try:
            parsed_dates.append(date.fromisoformat(str(iso_date)))
        except (TypeError, ValueError):
            continue
    return sorted(set(parsed_dates))


def build_chart_dataframe(
    start_date: date,
    end_date: date,
    cdi_rates: dict[str, float],
    usd_rates: dict[str, float],
    initial_brl: float,
) -> pd.DataFrame:
    """Prepare the comparative chart dataset for the Streamlit UI."""
    validate_inputs(start_date=start_date, end_date=end_date, initial_brl=initial_brl)
    effective_start_date, effective_end_date = resolve_cdi_period(
        cdi_rates=cdi_rates,
        start_date=start_date,
        end_date=end_date,
    )
    quote_resolver = QuoteResolver(usd_rates=usd_rates)
    initial_quote = quote_resolver.lookup(effective_start_date)
    timeline = [
        current_date
        for current_date in _valid_cdi_dates(cdi_rates)
        if effective_start_date <= current_date <= effective_end_date
    ]

    rows: list[dict[str, object]] = []
    cdi_factor = 1.0
    for current_date in timeline:
        effective_quote = quote_resolver.lookup(current_date)
        usd_variation = (effective_quote.value / initial_quote.value) - 1
        cdi_variation = cdi_factor - 1
        gain_real_usd = ((1 + cdi_variation) / (1 + usd_variation)) - 1

        rows.append(
            {
                "data": current_date,
                "CDI Acumulado (%)": cdi_variation * 100,
                "USD Acumulado (%)": usd_variation * 100,
                "Ganho Real em USD (%)": gain_real_usd * 100,
                "Capital Corrigido (BRL)": initial_brl * cdi_factor,
                "Cotacao USD/BRL": effective_quote.value,
            }
        )

        if current_date < effective_end_date:
            cdi_factor *= 1 + (cdi_rates[current_date.isoformat()] / 100)

    return pd.DataFrame(rows)
