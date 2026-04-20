from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from armadilha_cdi.services.calculations import lookup_quote_with_fallback, validate_inputs


def build_chart_dataframe(
    start_date: date,
    end_date: date,
    cdi_rates: dict[str, float],
    usd_rates: dict[str, float],
    initial_brl: float,
) -> pd.DataFrame:
    """Prepare the comparative chart dataset for the Streamlit UI."""
    validate_inputs(start_date=start_date, end_date=end_date, initial_brl=initial_brl)
    initial_quote = lookup_quote_with_fallback(usd_rates=usd_rates, target_date=start_date)
    timeline = pd.date_range(start=start_date, end=end_date, freq="D")

    rows: list[dict[str, object]] = []
    cdi_factor = 1.0
    for timestamp in timeline:
        current_date = timestamp.date()
        previous_day = current_date - timedelta(days=1)
        if start_date <= previous_day < end_date:
            previous_day_key = previous_day.isoformat()
            if previous_day_key in cdi_rates:
                cdi_factor *= 1 + (cdi_rates[previous_day_key] / 100)

        effective_quote = lookup_quote_with_fallback(usd_rates=usd_rates, target_date=current_date)
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

    return pd.DataFrame(rows)
