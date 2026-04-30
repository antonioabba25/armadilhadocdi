from __future__ import annotations

from datetime import date
import unittest

from armadilha_cdi.exceptions import DataUnavailableError, DomainValidationError
from armadilha_cdi.services.calculations import (
    QuoteResolver,
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

    def test_calculation_resolves_non_business_dates_to_previous_cdi_date(self) -> None:
        result = calculate_result(
            start_date=date(2024, 1, 6),
            end_date=date(2024, 1, 9),
            initial_brl=1000.0,
            cdi_rates={
                "2024-01-05": 0.10,
                "2024-01-08": 0.20,
                "2024-01-09": 0.30,
            },
            usd_rates={
                "2024-01-05": 5.00,
                "2024-01-08": 5.10,
                "2024-01-09": 5.20,
            },
        )

        expected_factor = (1 + 0.10 / 100) * (1 + 0.20 / 100)
        self.assertEqual(result.effective_start_date, date(2024, 1, 5))
        self.assertEqual(result.effective_end_date, date(2024, 1, 9))
        self.assertEqual(result.initial_fx_date, date(2024, 1, 5))
        self.assertAlmostEqual(result.cdi_factor, expected_factor, places=10)
        self.assertEqual(result.cdi_days_used, 2)

    def test_calculation_keeps_effective_end_as_exclusive_boundary(self) -> None:
        result = calculate_result(
            start_date=date(2024, 1, 4),
            end_date=date(2024, 1, 7),
            initial_brl=1000.0,
            cdi_rates={
                "2024-01-04": 0.10,
                "2024-01-05": 0.20,
            },
            usd_rates={
                "2024-01-04": 5.00,
                "2024-01-05": 5.10,
            },
        )

        self.assertEqual(result.effective_end_date, date(2024, 1, 5))
        self.assertAlmostEqual(result.cdi_factor, 1 + 0.10 / 100, places=10)
        self.assertEqual(result.cdi_days_used, 1)

    def test_invalid_period_is_rejected(self) -> None:
        with self.assertRaises(DomainValidationError):
            calculate_result(
                start_date=date(2024, 1, 3),
                end_date=date(2024, 1, 3),
                initial_brl=1000.0,
                cdi_rates=self.cdi_rates,
                usd_rates=self.usd_rates,
            )

    def test_start_date_before_real_circulation_is_rejected(self) -> None:
        with self.assertRaisesRegex(DomainValidationError, "01/07/1994"):
            calculate_result(
                start_date=date(1994, 6, 30),
                end_date=date(1994, 7, 4),
                initial_brl=1000.0,
                cdi_rates={
                    "1994-06-30": 0.10,
                    "1994-07-01": 0.20,
                    "1994-07-04": 0.30,
                },
                usd_rates={
                    "1994-06-30": 1.00,
                    "1994-07-01": 1.00,
                    "1994-07-04": 1.00,
                },
            )

    def test_real_circulation_start_date_does_not_fallback_to_previous_currency(self) -> None:
        result = calculate_result(
            start_date=date(1994, 7, 1),
            end_date=date(1994, 7, 4),
            initial_brl=1000.0,
            cdi_rates={
                "1994-06-30": 99.00,
                "1994-07-01": 0.20,
                "1994-07-04": 0.30,
            },
            usd_rates={
                "1994-06-30": 99.00,
                "1994-07-01": 1.00,
                "1994-07-04": 1.00,
            },
        )

        self.assertEqual(result.effective_start_date, date(1994, 7, 1))
        self.assertEqual(result.initial_fx_date, date(1994, 7, 1))
        self.assertAlmostEqual(result.cdi_factor, 1 + 0.20 / 100, places=10)

    def test_missing_quote_raises_data_unavailable(self) -> None:
        with self.assertRaises(DataUnavailableError):
            lookup_quote_with_fallback(
                usd_rates={},
                target_date=date(2024, 1, 3),
            )

    def test_quote_resolver_rejects_quote_outside_fallback_window(self) -> None:
        resolver = QuoteResolver(
            usd_rates={"2024-01-01": 5.00},
            max_days_back=2,
        )

        with self.assertRaises(DataUnavailableError):
            resolver.lookup(date(2024, 1, 4))

    def test_calculation_ignores_invalid_market_rows(self) -> None:
        result = calculate_result(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            initial_brl=1000.0,
            cdi_rates={
                **self.cdi_rates,
                "invalid-date": 99,
                "2024-01-02-extra": 99,
                None: 99,
            },
            usd_rates={
                **self.usd_rates,
                "invalid-date": 99,
            },
        )

        expected_factor = (1 + 0.10 / 100) * (1 + 0.20 / 100)
        self.assertAlmostEqual(result.cdi_factor, expected_factor, places=10)


if __name__ == "__main__":
    unittest.main()
