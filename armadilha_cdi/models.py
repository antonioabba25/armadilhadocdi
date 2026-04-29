from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class QuoteLookup:
    requested_date: date
    effective_date: date
    value: float


@dataclass(frozen=True)
class MarketDataBundle:
    cdi_rates: dict[str, float]
    usd_rates: dict[str, float]


@dataclass(frozen=True)
class CalculationResult:
    start_date: date
    end_date: date
    effective_start_date: date
    effective_end_date: date
    initial_brl: float
    final_brl: float
    cdi_factor: float
    cdi_percentage: float
    initial_usd: float
    final_usd_with_cdi: float
    initial_usdbrl: float
    final_usdbrl: float
    initial_fx_date: date
    final_fx_date: date
    real_usd_return_percentage: float
    cdi_days_used: int

    @property
    def period_label(self) -> str:
        return f"{self.start_date.strftime('%d/%m/%Y')} a {self.end_date.strftime('%d/%m/%Y')}"

    @property
    def effective_period_label(self) -> str:
        return (
            f"{self.effective_start_date.strftime('%d/%m/%Y')} "
            f"a {self.effective_end_date.strftime('%d/%m/%Y')}"
        )
