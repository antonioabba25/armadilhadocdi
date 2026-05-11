from __future__ import annotations

from datetime import date
import tempfile
import unittest
from pathlib import Path

from armadilha_cdi.models import MarketDataBundle
from scripts.export_static_market_data import (
    DATASET_FILENAME,
    MANIFEST_FILENAME,
    build_manifest,
    build_static_dataset,
    validate_static_dataset,
    write_json_atomic,
)


class StaticExportTests(unittest.TestCase):
    def test_build_static_dataset_normalizes_and_validates_series(self) -> None:
        dataset = build_static_dataset(
            requested_start_date=date(2024, 1, 1),
            requested_end_date=date(2024, 1, 5),
            generated_at="2026-05-11T00:00:00Z",
            market_data=MarketDataBundle(
                cdi_rates={
                    "2024-01-02": 0.10,
                    "invalid": 99.0,
                    "2024-01-03": "0.20",
                    "2024-01-06": 0.30,
                },
                usd_rates={
                    "2024-01-01": 5.00,
                    "2024-01-03": "5.10",
                    "2024-01-06": 5.20,
                },
            ),
        )

        self.assertEqual(dataset["schema_version"], 1)
        self.assertEqual(dataset["coverage"]["start_date"], "2024-01-01")
        self.assertEqual(dataset["coverage"]["end_date"], "2024-01-03")
        self.assertEqual(list(dataset["cdi_rates"]), ["2024-01-02", "2024-01-03"])
        self.assertEqual(list(dataset["usd_rates"]), ["2024-01-01", "2024-01-03"])

    def test_validate_static_dataset_rejects_sensitive_text(self) -> None:
        dataset = build_static_dataset(
            requested_start_date=date(2024, 1, 1),
            requested_end_date=date(2024, 1, 3),
            generated_at="2026-05-11T00:00:00Z",
            market_data=MarketDataBundle(
                cdi_rates={"2024-01-01": 0.10, "2024-01-02": 0.20},
                usd_rates={"2024-01-01": 5.00, "2024-01-02": 5.10},
            ),
        )
        dataset["source"]["cdi"] = "postgresql://secret"

        with self.assertRaisesRegex(ValueError, "segredo"):
            validate_static_dataset(dataset)

    def test_manifest_and_atomic_writes_use_expected_names(self) -> None:
        dataset = build_static_dataset(
            requested_start_date=date(2024, 1, 1),
            requested_end_date=date(2024, 1, 3),
            generated_at="2026-05-11T00:00:00Z",
            market_data=MarketDataBundle(
                cdi_rates={"2024-01-01": 0.10, "2024-01-02": 0.20},
                usd_rates={"2024-01-01": 5.00, "2024-01-02": 5.10},
            ),
        )
        manifest = build_manifest(dataset)

        self.assertEqual(manifest["latest"], DATASET_FILENAME)
        self.assertEqual(manifest["counts"]["cdi_rates"], 2)
        self.assertEqual(manifest["counts"]["usd_rates"], 2)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_json_atomic(root / DATASET_FILENAME, dataset)
            write_json_atomic(root / MANIFEST_FILENAME, manifest)

            self.assertTrue((root / DATASET_FILENAME).exists())
            self.assertTrue((root / MANIFEST_FILENAME).exists())


if __name__ == "__main__":
    unittest.main()
