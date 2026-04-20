from __future__ import annotations

import json
from pathlib import Path


class JsonFileCache:
    """Simple file-based cache for time series keyed by ISO date."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name: str) -> dict[str, float]:
        path = self.root_dir / name
        if not path.exists():
            return {}

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(raw_data, dict):
            return {}

        normalized: dict[str, float] = {}
        for key, value in raw_data.items():
            try:
                normalized[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized

    def save(self, name: str, data: dict[str, float]) -> None:
        path = self.root_dir / name
        serialized = {key: data[key] for key in sorted(data)}
        path.write_text(
            json.dumps(serialized, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def merge(self, name: str, new_data: dict[str, float]) -> dict[str, float]:
        cached = self.load(name)
        cached.update(new_data)
        self.save(name, cached)
        return cached
