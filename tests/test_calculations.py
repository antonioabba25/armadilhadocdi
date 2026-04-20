from __future__ import annotations

from datetime import date
import unittest

from armadilha_cdi.exceptions import DataUnavailableError, DomainValidationError
from armadilha_cdi.services.calculations import (
    calculate_result,
    lookup_quote_with_fallback,
)


class CalculationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cdi_rates = {
            "2024-01-01": 0.10,
            "2024-01-02": 0.20,
            "2024-01-03": 0.30,
        }
        self.usd_rates = {
            "2023-12-29": 4.90,
            "2024-01-01": 5.00,
            "2024-01-03": 5.20,
            "2024-01-04": 5.30,
        }

    def test_calculation_uses_start_inclusive_end_exclusive(self) -> None:
        result = calculate_result(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            initial_brl=1000.0,
            cdi_rates=self.cdi_rates,
            usd_rates=self.usd_rates,
        )

        expected_factor = (1 + 0.10 / 100) * (1 + 0.20 / 100)
        self.assertAlmostEqual(result.cdi_factor, expected_factor, places=10)
        self.assertEqual(result.cdi_days_used, 2)

    def test_uses_previous_quote_when_target_date_has_no_exact_quote(self) -> None:
        quote = lookup_quote_with_fallback(
            usd_rates=self.usd_rates,
            target_date=date(2024, 1, 2),
        )

        self.assertEqual(quote.effective_date, date(2024, 1, 1))
        self.assertEqual(quote.value, 5.00)

    def test_invalid_period_is_rejected(self) -> None:
        with self.assertRaises(DomainValidationError):
            calculate_result(
                start_date=date(2024, 1, 3),
                end_date=date(2024, 1, 3),
                initial_brl=1000.0,
                cdi_rates=self.cdi_rates,
                usd_rates=self.usd_rates,
            )

    def test_missing_quote_raises_data_unavailable(self) -> None:
        with self.assertRaises(DataUnavailableError):
            lookup_quote_with_fallback(
                usd_rates={},
                target_date=date(2024, 1, 3),
            )


if __name__ == "__main__":
    unittest.main()
