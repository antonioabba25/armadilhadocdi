from __future__ import annotations

from datetime import date
import unittest

from armadilha_cdi import frontpage_texts as copy
from armadilha_cdi.services.charts import build_chart_dataframe


class ChartTests(unittest.TestCase):
    def test_chart_dataframe_contains_expected_series(self) -> None:
        cdi_rates = {
            "2024-01-01": 0.10,
            "2024-01-02": 0.10,
            "2024-01-03": 0.10,
        }
        usd_rates = {
            "2024-01-01": 5.00,
            "2024-01-03": 5.10,
        }

        dataframe = build_chart_dataframe(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3),
            cdi_rates=cdi_rates,
            usd_rates=usd_rates,
            initial_brl=1000.0,
        )

        self.assertEqual(
            list(dataframe.columns),
            [
                copy.CHART_DATE,
                copy.CHART_CDI_ACCUMULATED,
                copy.CHART_USD_ACCUMULATED,
                copy.CHART_USD_PERCENT_VARIATION,
                copy.CHART_ADJUSTED_CAPITAL,
                copy.CHART_USD_BRL_QUOTE,
            ],
        )
        self.assertEqual(len(dataframe), 3)
        self.assertAlmostEqual(
            dataframe.iloc[0][copy.CHART_CDI_ACCUMULATED], 0.0, places=6
        )
        self.assertAlmostEqual(
            dataframe.iloc[-1][copy.CHART_USD_ACCUMULATED], 2.0, places=6
        )

    def test_chart_dataframe_uses_only_official_business_dates(self) -> None:
        dataframe = build_chart_dataframe(
            start_date=date(2024, 1, 6),
            end_date=date(2024, 1, 9),
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
            initial_brl=1000.0,
        )

        self.assertEqual(
            dataframe["data"].tolist(),
            [
                date(2024, 1, 5),
                date(2024, 1, 8),
                date(2024, 1, 9),
            ],
        )
        expected_cdi = ((1 + 0.10 / 100) * (1 + 0.20 / 100) - 1) * 100
        self.assertAlmostEqual(
            dataframe.iloc[-1][copy.CHART_CDI_ACCUMULATED], expected_cdi
        )

    def test_chart_dataframe_uses_same_initial_quote_fallback_as_calculation(self) -> None:
        dataframe = build_chart_dataframe(
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 3),
            cdi_rates={
                "2024-01-02": 0.10,
                "2024-01-03": 0.20,
            },
            usd_rates={
                "2023-12-29": 4.90,
                "2024-01-03": 5.00,
            },
            initial_brl=1000.0,
        )

        self.assertEqual(len(dataframe), 2)
        self.assertAlmostEqual(dataframe.iloc[0][copy.CHART_USD_BRL_QUOTE], 4.90)
        self.assertAlmostEqual(
            dataframe.iloc[-1][copy.CHART_USD_ACCUMULATED],
            ((5.00 / 4.90) - 1) * 100,
        )


if __name__ == "__main__":
    unittest.main()
