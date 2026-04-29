from __future__ import annotations

from datetime import date
import unittest

from armadilha_cdi.services.data_providers import BCBMarketDataProvider


class MarketDataProviderTests(unittest.TestCase):
    def test_covers_window_ignores_invalid_cache_keys(self) -> None:
        self.assertTrue(
            BCBMarketDataProvider._covers_window(
                series={
                    "invalid-date": 1.0,
                    None: 2.0,
                    "2024-01-01": 0.1,
                    "2024-01-10": 0.2,
                },
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 10),
                tolerance_days=0,
            )
        )

    def test_covers_window_rejects_cache_without_valid_dates(self) -> None:
        self.assertFalse(
            BCBMarketDataProvider._covers_window(
                series={"invalid-date": 1.0},
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 10),
                tolerance_days=0,
            )
        )


if __name__ == "__main__":
    unittest.main()
