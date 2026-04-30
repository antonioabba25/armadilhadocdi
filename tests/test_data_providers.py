from __future__ import annotations

from datetime import date
import unittest
from unittest import mock

import requests

from armadilha_cdi.exceptions import MarketDataError
from armadilha_cdi.services.data_providers import BCBMarketDataProvider


class FakeResponse:
    def __init__(
        self,
        payload: object | None = None,
        status_code: int = 200,
        text: str = "",
    ) -> None:
        self.payload = payload
        self.status_code = status_code
        self.text = text

    def json(self) -> object:
        if self.payload is None:
            raise ValueError("invalid json")
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            error = requests.HTTPError(f"{self.status_code} error")
            error.response = self  # type: ignore[assignment]
            raise error


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

    def test_get_market_data_rejects_start_date_before_real_circulation(self) -> None:
        provider = BCBMarketDataProvider(cache_repository=mock.Mock())

        with self.assertRaisesRegex(MarketDataError, "01/07/1994"):
            provider.get_market_data(
                start_date=date(1994, 6, 30),
                end_date=date(1994, 7, 4),
            )

    def test_get_market_data_does_not_fetch_before_real_circulation(self) -> None:
        provider = BCBMarketDataProvider(cache_repository=mock.Mock())
        provider._ensure_cdi_data = mock.Mock(return_value={})  # type: ignore[method-assign]
        provider._ensure_usd_data = mock.Mock(return_value={})  # type: ignore[method-assign]

        provider.get_market_data(
            start_date=date(1994, 7, 1),
            end_date=date(1994, 7, 4),
        )

        provider._ensure_cdi_data.assert_called_once_with(
            start_date=date(1994, 7, 1),
            end_date=date(1994, 7, 4),
        )
        provider._ensure_usd_data.assert_called_once_with(
            start_date=date(1994, 7, 1),
            end_date=date(1994, 7, 4),
        )

    def test_fetch_cdi_rates_splits_requests_and_waits_between_chunks(self) -> None:
        sleep_func = mock.Mock()
        provider = BCBMarketDataProvider(
            cache_repository=mock.Mock(),
            cdi_chunk_days=2,
            cdi_chunk_delay_seconds=0.5,
            sleep_func=sleep_func,
        )

        responses = [
            FakeResponse([{"data": "01/01/2024", "valor": "0.01"}]),
            FakeResponse([{"data": "03/01/2024", "valor": "0.02"}]),
            FakeResponse([{"data": "05/01/2024", "valor": "0.03"}]),
        ]

        with mock.patch(
            "armadilha_cdi.services.data_providers.requests.get",
            side_effect=responses,
        ) as requests_get:
            result = provider._fetch_cdi_rates(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 5),
            )

        self.assertEqual(
            result,
            {
                "2024-01-01": 0.01,
                "2024-01-03": 0.02,
                "2024-01-05": 0.03,
            },
        )
        self.assertEqual(requests_get.call_count, 3)
        requested_params = [call.kwargs["params"] for call in requests_get.call_args_list]
        self.assertEqual(
            requested_params,
            [
                {
                    "formato": "json",
                    "dataInicial": "01/01/2024",
                    "dataFinal": "02/01/2024",
                },
                {
                    "formato": "json",
                    "dataInicial": "03/01/2024",
                    "dataFinal": "04/01/2024",
                },
                {
                    "formato": "json",
                    "dataInicial": "05/01/2024",
                    "dataFinal": "05/01/2024",
                },
            ],
        )
        sleep_func.assert_has_calls([mock.call(0.5), mock.call(0.5)])

    def test_fetch_cdi_rates_uses_bcb_json_error_message(self) -> None:
        provider = BCBMarketDataProvider(cache_repository=mock.Mock())

        with mock.patch(
            "armadilha_cdi.services.data_providers.requests.get",
            return_value=FakeResponse(
                {"message": "janela maxima excedida"},
                status_code=406,
            ),
        ):
            with self.assertRaisesRegex(MarketDataError, "janela maxima excedida"):
                provider._fetch_cdi_rates_chunk(
                    start_date=date(1996, 12, 16),
                    end_date=date(2026, 3, 31),
                )

    def test_fetch_cdi_rates_rejects_html_error_with_status_ok(self) -> None:
        provider = BCBMarketDataProvider(cache_repository=mock.Mock())

        with mock.patch(
            "armadilha_cdi.services.data_providers.requests.get",
            return_value=FakeResponse(
                payload=None,
                text="<title>Requisicao invalida!</title>",
            ),
        ):
            with self.assertRaisesRegex(MarketDataError, "pagina HTML"):
                provider._fetch_cdi_rates_chunk(
                    start_date=date(2025, 1, 1),
                    end_date=date(2026, 3, 31),
                )


if __name__ == "__main__":
    unittest.main()
