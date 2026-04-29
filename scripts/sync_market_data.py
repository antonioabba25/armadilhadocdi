from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from armadilha_cdi.config import DEFAULT_CACHE_DIR, EARLIEST_SUPPORTED_DATE
from armadilha_cdi.services.cache import JsonFileCache
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

    provider = BCBMarketDataProvider(
        cache_repository=JsonFileCache(args.cache_dir),
    )
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
