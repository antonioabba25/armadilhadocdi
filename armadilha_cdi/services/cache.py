from __future__ import annotations

from contextlib import contextmanager
from datetime import date
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from typing import ClassVar, Iterator, Protocol

from armadilha_cdi.config import DEFAULT_CACHE_DIR, DEFAULT_SUPABASE_CACHE_TABLE

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows fallback, kept harmless for local dev.
    fcntl = None  # type: ignore[assignment]


class TimeSeriesCache(Protocol):
    """Persistence contract for time series keyed by ISO date."""

    def load(self, name: str) -> dict[str, float]:
        """Load all cached values for a named series."""

    def save(self, name: str, data: dict[str, float]) -> None:
        """Replace all cached values for a named series."""

    def merge(self, name: str, new_data: dict[str, float]) -> dict[str, float]:
        """Merge new values into a named series and return the full cached series."""


class CacheConfigurationError(RuntimeError):
    """Raised when the configured cache backend cannot be initialized."""


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


class PostgresTimeSeriesCache:
    """Postgres-backed cache for Supabase deployments."""

    _table_name_pattern: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(
        self,
        database_url: str,
        table_name: str = DEFAULT_SUPABASE_CACHE_TABLE,
        connect_timeout_seconds: int = 10,
        ensure_schema: bool = True,
    ) -> None:
        if not database_url:
            raise CacheConfigurationError(
                "Defina SUPABASE_DATABASE_URL ou DATABASE_URL para usar o cache Supabase."
            )

        self.database_url = database_url
        self.table_name = self._validate_table_name(table_name)
        self.connect_timeout_seconds = connect_timeout_seconds

        if ensure_schema:
            self._ensure_schema()

    def load(self, name: str) -> dict[str, float]:
        with self._connect() as connection:
            return self._load_with_connection(connection, name)

    def save(self, name: str, data: dict[str, float]) -> None:
        series = self._series_name(name)
        normalized = self._normalize_data(data)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"delete from {self.table_name} where series = %s",
                    (series,),
                )
                self._insert_rows(cursor, series, normalized)

    def merge(self, name: str, new_data: dict[str, float]) -> dict[str, float]:
        series = self._series_name(name)
        normalized = self._normalize_data(new_data)

        with self._connect() as connection:
            with connection.cursor() as cursor:
                self._insert_rows(cursor, series, normalized)
            return self._load_with_connection(connection, name)

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - depends on optional runtime package.
            raise CacheConfigurationError(
                "Instale a dependencia psycopg[binary] para usar o cache Supabase."
            ) from exc

        return psycopg.connect(
            self.database_url,
            connect_timeout=self.connect_timeout_seconds,
            prepare_threshold=None,
        )

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    create table if not exists {self.table_name} (
                        series text not null,
                        ref_date date not null,
                        value numeric not null,
                        updated_at timestamptz not null default now(),
                        primary key (series, ref_date)
                    )
                    """
                )

    def _load_with_connection(self, connection, name: str) -> dict[str, float]:
        series = self._series_name(name)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                select ref_date, value
                from {self.table_name}
                where series = %s
                order by ref_date
                """,
                (series,),
            )
            rows = cursor.fetchall()

        loaded: dict[str, float] = {}
        for row_date, row_value in rows:
            if isinstance(row_date, date):
                key = row_date.isoformat()
            else:
                key = str(row_date)
            loaded[key] = float(row_value)
        return loaded

    def _insert_rows(
        self,
        cursor,
        series: str,
        data: dict[str, float],
    ) -> None:
        if not data:
            return

        cursor.executemany(
            f"""
            insert into {self.table_name} (series, ref_date, value, updated_at)
            values (%s, %s, %s, now())
            on conflict (series, ref_date) do update
            set value = excluded.value,
                updated_at = now()
            """,
            [(series, iso_date, value) for iso_date, value in sorted(data.items())],
        )

    @classmethod
    def _validate_table_name(cls, table_name: str) -> str:
        normalized = table_name.strip()
        if not cls._table_name_pattern.fullmatch(normalized):
            raise CacheConfigurationError(
                "SUPABASE_CACHE_TABLE deve conter apenas letras, numeros e underscore, "
                "comecando por letra ou underscore."
            )
        return normalized

    @staticmethod
    def _series_name(name: str) -> str:
        return Path(name).stem

    @staticmethod
    def _normalize_data(data: dict[str, float]) -> dict[str, float]:
        normalized: dict[str, float] = {}
        for key, value in data.items():
            try:
                iso_date = date.fromisoformat(str(key)).isoformat()
                normalized[iso_date] = float(value)
            except (TypeError, ValueError):
                continue
        return normalized


def build_cache_repository(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    backend: str | None = None,
    database_url: str | None = None,
    table_name: str | None = None,
) -> TimeSeriesCache:
    """Build the configured cache backend.

    The default remains JSON for local development. Use
    MARKET_DATA_CACHE_BACKEND=supabase with SUPABASE_DATABASE_URL in production.
    """

    selected_backend = (backend or os.getenv("MARKET_DATA_CACHE_BACKEND") or "json").strip().lower()

    if selected_backend in {"json", "file", "local"}:
        return JsonFileCache(cache_dir)

    if selected_backend in {"supabase", "postgres", "postgresql"}:
        selected_database_url = (
            database_url
            or os.getenv("SUPABASE_DATABASE_URL")
            or os.getenv("DATABASE_URL")
            or ""
        )
        selected_table_name = (
            table_name
            or os.getenv("SUPABASE_CACHE_TABLE")
            or DEFAULT_SUPABASE_CACHE_TABLE
        )
        return PostgresTimeSeriesCache(
            database_url=selected_database_url,
            table_name=selected_table_name,
        )

    raise CacheConfigurationError(
        "MARKET_DATA_CACHE_BACKEND deve ser json, supabase, postgres ou postgresql."
    )
