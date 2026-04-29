from __future__ import annotations

from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / "cache"

DATE_STORAGE_FORMAT = "%Y-%m-%d"
DATE_DISPLAY_FORMAT = "%d/%m/%Y"
PTAX_QUERY_FORMAT = "%m-%d-%Y"

EARLIEST_SUPPORTED_DATE = date(1986, 3, 6)
MAX_USD_FALLBACK_DAYS = 15
MAX_MARKET_DATE_FALLBACK_DAYS = 15
REQUEST_TIMEOUT_SECONDS = 20

BCB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

CDI_SERIES_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"
PTAX_URL_TEMPLATE = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
    "@dataInicial='{start}'&@dataFinalCotacao='{end}'"
    "&$format=json&$select=cotacaoVenda,dataHoraCotacao"
)
