from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from armadilha_cdi.services.cache import (
    CacheConfigurationError,
    JsonFileCache,
    PostgresTimeSeriesCache,
    build_cache_repository,
)


class JsonFileCacheTests(unittest.TestCase):
    def test_merge_preserves_existing_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = JsonFileCache(Path(temp_dir))

            cache.save("series.json", {"2024-01-01": 1.0})
            merged = cache.merge("series.json", {"2024-01-02": 2.0})

            self.assertEqual(
                merged,
                {
                    "2024-01-01": 1.0,
                    "2024-01-02": 2.0,
                },
            )
            self.assertEqual(cache.load("series.json"), merged)

    def test_load_ignores_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            (cache_dir / "series.json").write_text("{invalid", encoding="utf-8")

            self.assertEqual(JsonFileCache(cache_dir).load("series.json"), {})

    def test_rejects_cache_names_outside_root_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = JsonFileCache(Path(temp_dir))

            with self.assertRaises(ValueError):
                cache.load("../series.json")

    def test_save_replaces_file_with_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = JsonFileCache(Path(temp_dir))

            cache.save("series.json", {"2024-01-02": 2.0, "2024-01-01": 1.0})

            raw_data = json.loads((Path(temp_dir) / "series.json").read_text("utf-8"))
            self.assertEqual(list(raw_data), ["2024-01-01", "2024-01-02"])

    def test_parallel_merges_keep_all_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = JsonFileCache(Path(temp_dir))

            def merge_value(index: int) -> None:
                cache.merge("series.json", {f"2024-01-{index + 1:02d}": float(index)})

            with ThreadPoolExecutor(max_workers=8) as executor:
                list(executor.map(merge_value, range(20)))

            self.assertEqual(len(cache.load("series.json")), 20)


class CacheFactoryTests(unittest.TestCase):
    def test_build_cache_repository_defaults_to_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(os.environ, {"MARKET_DATA_CACHE_BACKEND": ""}):
                cache = build_cache_repository(cache_dir=Path(temp_dir))

            self.assertIsInstance(cache, JsonFileCache)

    def test_build_cache_repository_rejects_unknown_backend(self) -> None:
        with self.assertRaises(CacheConfigurationError):
            build_cache_repository(backend="memory")

    def test_build_cache_repository_requires_database_url_for_supabase(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SUPABASE_DATABASE_URL": "", "DATABASE_URL": ""},
        ):
            with self.assertRaises(CacheConfigurationError):
                build_cache_repository(backend="supabase", database_url="")


class PostgresTimeSeriesCacheTests(unittest.TestCase):
    def test_rejects_unsafe_table_name_before_connecting(self) -> None:
        with self.assertRaises(CacheConfigurationError):
            PostgresTimeSeriesCache(
                database_url="postgresql://example",
                table_name="market_rates; drop table market_rates",
                ensure_schema=False,
            )

    def test_normalize_data_keeps_only_valid_dates_and_numbers(self) -> None:
        self.assertEqual(
            PostgresTimeSeriesCache._normalize_data(
                {
                    "2024-01-01": "1.5",
                    "invalid": 2.0,
                    "2024-01-02": "not-a-number",
                }
            ),
            {"2024-01-01": 1.5},
        )


if __name__ == "__main__":
    unittest.main()
