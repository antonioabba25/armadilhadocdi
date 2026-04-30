from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from armadilha_cdi.config import (
    DEFAULT_CACHE_DIR,
    DEFAULT_SUPABASE_CACHE_TABLE,
    EARLIEST_SUPPORTED_DATE,
)
from armadilha_cdi.services.cache import CacheConfigurationError, build_cache_repository
from armadilha_cdi.services.data_providers import BCBMarketDataProvider


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use datas no formato YYYY-MM-DD.") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sincroniza o cache local de CDI e USD/BRL com o Banco Central."
    )
    parser.add_argument(
        "--start",
        type=parse_iso_date,
        default=date.today() - timedelta(days=365),
        help="Data inicial da janela a sincronizar, em YYYY-MM-DD. Padrao: ultimos 365 dias.",
    )
    parser.add_argument(
        "--end",
        type=parse_iso_date,
        default=date.today(),
        help="Data final da janela a sincronizar, em YYYY-MM-DD. Padrao: hoje.",
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
        help=(
            "Backend do cache. Padrao: MARKET_DATA_CACHE_BACKEND ou json. "
            "Use supabase para gravar no Postgres do Supabase."
        ),
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help=(
            "URL Postgres do Supabase. Padrao: SUPABASE_DATABASE_URL ou DATABASE_URL."
        ),
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
    market_data = provider.get_market_data(
        start_date=args.start,
        end_date=args.end,
    )

    print(
        "Cache sincronizado: "
        f"{len(market_data.cdi_rates)} pontos de CDI, "
        f"{len(market_data.usd_rates)} pontos de USD/BRL."
    )


if __name__ == "__main__":
    main()
