from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import ClassVar, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback, kept harmless for local dev.
    fcntl = None  # type: ignore[assignment]


class JsonFileCache:
    """File-based cache for time series keyed by ISO date."""

    _registry_lock: ClassVar[threading.Lock] = threading.Lock()
    _locks_by_path: ClassVar[dict[Path, threading.RLock]] = {}

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name: str) -> dict[str, float]:
        with self._locked(name):
            return self._load_unlocked(name)

    def save(self, name: str, data: dict[str, float]) -> None:
        with self._locked(name):
            self._save_unlocked(name, data)

    def merge(self, name: str, new_data: dict[str, float]) -> dict[str, float]:
        with self._locked(name):
            cached = self._load_unlocked(name)
            cached.update(new_data)
            self._save_unlocked(name, cached)
            return cached

    @contextmanager
    def _locked(self, name: str) -> Iterator[None]:
        lock_path = self.root_dir / f"{name}.lock"
        thread_lock = self._thread_lock_for(lock_path)

        with thread_lock:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("a+", encoding="utf-8") as lock_file:
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if fcntl is not None:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @classmethod
    def _thread_lock_for(cls, lock_path: Path) -> threading.RLock:
        resolved = lock_path.resolve()
        with cls._registry_lock:
            if resolved not in cls._locks_by_path:
                cls._locks_by_path[resolved] = threading.RLock()
            return cls._locks_by_path[resolved]

    def _load_unlocked(self, name: str) -> dict[str, float]:
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

    def _save_unlocked(self, name: str, data: dict[str, float]) -> None:
        path = self.root_dir / name
        serialized = {key: data[key] for key in sorted(data)}
        payload = json.dumps(serialized, ensure_ascii=True, indent=2)

        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.root_dir,
            prefix=f".{name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(payload)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)

        try:
            os.replace(temp_path, path)
        finally:
            if temp_path.exists():
                temp_path.unlink()
