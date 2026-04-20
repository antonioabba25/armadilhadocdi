from __future__ import annotations

from datetime import date
import unittest

from armadilha_cdi.services.charts import build_chart_dataframe


class ChartTests(unittest.TestCase):
    def test_chart_dataframe_contains_expected_series(self) -> None:
        cdi_rates = {
            "2024-01-01": 0.10,
            "2024-01-02": 0.10,
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
                "data",
                "CDI Acumulado (%)",
                "USD Acumulado (%)",
                "Ganho Real em USD (%)",
                "Capital Corrigido (BRL)",
                "Cotacao USD/BRL",
            ],
        )
        self.assertEqual(len(dataframe), 3)
        self.assertAlmostEqual(dataframe.iloc[0]["CDI Acumulado (%)"], 0.0, places=6)
        self.assertAlmostEqual(dataframe.iloc[-1]["USD Acumulado (%)"], 2.0, places=6)


if __name__ == "__main__":
    unittest.main()
