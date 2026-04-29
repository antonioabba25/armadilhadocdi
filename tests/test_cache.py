from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest

from armadilha_cdi.services.cache import JsonFileCache


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


if __name__ == "__main__":
    unittest.main()
