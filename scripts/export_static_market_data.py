from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from armadilha_cdi.config import (  # noqa: E402
    DEFAULT_CACHE_DIR,
    DEFAULT_SUPABASE_CACHE_TABLE,
    EARLIEST_SUPPORTED_DATE,
    MAX_MARKET_DATE_FALLBACK_DAYS,
    MAX_USD_FALLBACK_DAYS,
)
from armadilha_cdi.models import MarketDataBundle  # noqa: E402
from armadilha_cdi.services.cache import (  # noqa: E402
    CacheConfigurationError,
    build_cache_repository,
)
from armadilha_cdi.services.data_providers import BCBMarketDataProvider  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "public" / "data"
DATASET_FILENAME = "market-data.latest.json"
MANIFEST_FILENAME = "market-data.manifest.json"
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SENSITIVE_TEXT_PATTERNS = (
    "postgresql://",
    "postgres://",
    "supabase_database_url",
    "database_url",
    "service_role",
    "anon key",
    "password=",
)


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use datas no formato YYYY-MM-DD.") from exc


def _utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _normalize_series(series: dict[str, float], end_date: date) -> dict[str, float]:
    normalized: dict[str, float] = {}
    for raw_key, raw_value in series.items():
        try:
            parsed_date = date.fromisoformat(str(raw_key))
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if parsed_date < EARLIEST_SUPPORTED_DATE or parsed_date > end_date:
            continue
        if value != value or value in (float("inf"), float("-inf")):
            continue
        normalized[parsed_date.isoformat()] = value
    return {key: normalized[key] for key in sorted(normalized)}


def _series_bounds(series: dict[str, float]) -> tuple[str, str]:
    if not series:
        raise ValueError("Serie vazia.")
    keys = sorted(series)
    return keys[0], keys[-1]


def build_static_dataset(
    *,
    requested_start_date: date,
    requested_end_date: date,
    market_data: MarketDataBundle,
    generated_at: str | None = None,
) -> dict[str, Any]:
    cdi_rates = _normalize_series(market_data.cdi_rates, requested_end_date)
    usd_rates = _normalize_series(market_data.usd_rates, requested_end_date)

    cdi_start, cdi_end = _series_bounds(cdi_rates)
    usd_start, usd_end = _series_bounds(usd_rates)
    common_end = min(cdi_end, usd_end, requested_end_date.isoformat())

    dataset: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _utc_now_iso(),
        "source": {
            "cdi": "BCB SGS serie 12",
            "usdbrl": "BCB Olinda PTAX venda",
        },
        "coverage": {
            "requested_start_date": requested_start_date.isoformat(),
            "requested_end_date": requested_end_date.isoformat(),
            "start_date": requested_start_date.isoformat(),
            "end_date": common_end,
            "cdi_start_date": cdi_start,
            "cdi_end_date": cdi_end,
            "usd_start_date": usd_start,
            "usd_end_date": usd_end,
        },
        "limits": {
            "earliest_supported_date": EARLIEST_SUPPORTED_DATE.isoformat(),
            "max_usd_fallback_days": MAX_USD_FALLBACK_DAYS,
            "max_market_date_fallback_days": MAX_MARKET_DATE_FALLBACK_DAYS,
        },
        "cdi_rates": cdi_rates,
        "usd_rates": usd_rates,
    }
    validate_static_dataset(dataset)
    return dataset


def build_manifest(dataset: dict[str, Any]) -> dict[str, Any]:
    coverage = dataset["coverage"]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dataset["generated_at"],
        "latest": DATASET_FILENAME,
        "coverage": {
            "start_date": coverage["start_date"],
            "end_date": coverage["end_date"],
        },
        "counts": {
            "cdi_rates": len(dataset["cdi_rates"]),
            "usd_rates": len(dataset["usd_rates"]),
        },
    }
    validate_manifest(manifest)
    return manifest


def validate_static_dataset(dataset: dict[str, Any]) -> None:
    if dataset.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version invalido no dataset estatico.")
    generated_at = dataset.get("generated_at")
    if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
        raise ValueError("generated_at deve ser uma string UTC terminada em Z.")
    for section in ("source", "coverage", "limits", "cdi_rates", "usd_rates"):
        if not isinstance(dataset.get(section), dict):
            raise ValueError(f"Secao ausente ou invalida: {section}.")

    coverage = dataset["coverage"]
    for key in (
        "requested_start_date",
        "requested_end_date",
        "start_date",
        "end_date",
        "cdi_start_date",
        "cdi_end_date",
        "usd_start_date",
        "usd_end_date",
    ):
        _require_iso_date(coverage.get(key), f"coverage.{key}")

    if date.fromisoformat(coverage["start_date"]) < EARLIEST_SUPPORTED_DATE:
        raise ValueError("coverage.start_date nao pode ser anterior a 1994-07-01.")
    if coverage["end_date"] > coverage["cdi_end_date"]:
        raise ValueError("coverage.end_date ultrapassa a cobertura do CDI.")
    if coverage["end_date"] > coverage["usd_end_date"]:
        raise ValueError("coverage.end_date ultrapassa a cobertura do USD/BRL.")

    for name in ("cdi_rates", "usd_rates"):
        series = dataset[name]
        if not series:
            raise ValueError(f"{name} nao pode ficar vazio.")
        previous_key = ""
        for key, value in series.items():
            _require_iso_date(key, name)
            if previous_key and key <= previous_key:
                raise ValueError(f"{name} deve estar ordenado por data.")
            previous_key = key
            if not isinstance(value, (int, float)) or value != value:
                raise ValueError(f"{name} contem valor numerico invalido em {key}.")

    serialized = json.dumps(dataset, ensure_ascii=True).lower()
    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern in serialized:
            raise ValueError("Dataset contem texto com aparencia de segredo ou credencial.")


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version invalido no manifesto.")
    if manifest.get("latest") != DATASET_FILENAME:
        raise ValueError("Manifesto aponta para arquivo latest inesperado.")
    _require_iso_date(manifest.get("coverage", {}).get("start_date"), "coverage.start_date")
    _require_iso_date(manifest.get("coverage", {}).get("end_date"), "coverage.end_date")
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        raise ValueError("Manifesto sem counts.")
    if int(counts.get("cdi_rates", 0)) <= 0 or int(counts.get("usd_rates", 0)) <= 0:
        raise ValueError("Manifesto aponta para dataset vazio.")


def _require_iso_date(value: object, label: str) -> None:
    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        raise ValueError(f"{label} deve usar YYYY-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} contem data invalida.") from exc


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    content += "\n"

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exporta CDI e USD/BRL para arquivos JSON estaticos."
    )
    parser.add_argument(
        "--start",
        type=parse_iso_date,
        default=EARLIEST_SUPPORTED_DATE,
        help="Data inicial da cobertura publica, em YYYY-MM-DD.",
    )
    parser.add_argument(
        "--end",
        type=parse_iso_date,
        default=date.today(),
        help="Data final a sincronizar, em YYYY-MM-DD. Padrao: hoje.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Diretorio de saida dos JSONs estaticos. Padrao: public/data.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="Diretorio do cache JSON. Padrao: cache/ do projeto.",
    )
    parser.add_argument(
        "--cache-backend",
        choices=("json", "supabase", "postgres", "postgresql"),
        default=None,
        help="Backend do cache. Padrao: MARKET_DATA_CACHE_BACKEND ou json.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="URL Postgres do Supabase. Padrao: SUPABASE_DATABASE_URL ou DATABASE_URL.",
    )
    parser.add_argument(
        "--cache-table",
        default=None,
        help=(
            "Tabela usada no Postgres. Padrao: SUPABASE_CACHE_TABLE ou "
            f"{DEFAULT_SUPABASE_CACHE_TABLE}."
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.start < EARLIEST_SUPPORTED_DATE:
        raise SystemExit(
            "A data inicial deve ser igual ou posterior a "
            f"{EARLIEST_SUPPORTED_DATE.isoformat()}."
        )
    if args.end <= args.start:
        raise SystemExit("A data final deve ser maior que a data inicial.")

    try:
        cache_repository = build_cache_repository(
            cache_dir=args.cache_dir,
            backend=args.cache_backend,
            database_url=args.database_url,
            table_name=args.cache_table,
        )
    except CacheConfigurationError as exc:
        raise SystemExit(str(exc)) from exc

    provider = BCBMarketDataProvider(cache_repository=cache_repository)
    market_data = provider.get_market_data(start_date=args.start, end_date=args.end)
    dataset = build_static_dataset(
        requested_start_date=args.start,
        requested_end_date=args.end,
        market_data=market_data,
    )
    manifest = build_manifest(dataset)

    dataset_path = args.output_dir / DATASET_FILENAME
    manifest_path = args.output_dir / MANIFEST_FILENAME
    write_json_atomic(dataset_path, dataset)
    write_json_atomic(manifest_path, manifest)

    dataset_size_kb = dataset_path.stat().st_size / 1024
    print(
        "Dataset estatico gerado: "
        f"{dataset_path} ({dataset_size_kb:.1f} KiB), "
        f"{len(dataset['cdi_rates'])} pontos CDI, "
        f"{len(dataset['usd_rates'])} pontos USD/BRL, "
        f"cobertura ate {dataset['coverage']['end_date']}."
    )


if __name__ == "__main__":
    main()
