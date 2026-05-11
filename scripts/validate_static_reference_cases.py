from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from armadilha_cdi.services.calculations import calculate_result  # noqa: E402
from scripts.export_static_market_data import (  # noqa: E402
    DATASET_FILENAME,
    validate_static_dataset,
)

DEFAULT_DATASET_PATH = PROJECT_ROOT / "public" / "data" / DATASET_FILENAME
DEFAULT_CASES_PATH = PROJECT_ROOT / "tests" / "fixtures" / "static_reference_periods.json"
JS_RUNNER_PATH = PROJECT_ROOT / "scripts" / "js_calculate_static.mjs"

FIELDS_TO_COMPARE = (
    "final_brl",
    "cdi_percentage",
    "effective_start_date",
    "effective_end_date",
    "initial_fx_date",
    "final_fx_date",
    "real_usd_return_percentage",
    "cdi_days_used",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compara os resultados Python e JavaScript usando o dataset estatico."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Caminho do market-data.latest.json.",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=DEFAULT_CASES_PATH,
        help="Arquivo JSON com periodos de referencia.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1e-7,
        help="Tolerancia numerica para campos de ponto flutuante.",
    )
    return parser


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Arquivo nao encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON invalido em {path}: {exc}") from exc


def _python_result(case: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    result = calculate_result(
        start_date=date.fromisoformat(case["start_date"]),
        end_date=date.fromisoformat(case["end_date"]),
        initial_brl=float(case["initial_brl"]),
        cdi_rates=dataset["cdi_rates"],
        usd_rates=dataset["usd_rates"],
    )
    return {
        "final_brl": result.final_brl,
        "cdi_percentage": result.cdi_percentage,
        "effective_start_date": result.effective_start_date.isoformat(),
        "effective_end_date": result.effective_end_date.isoformat(),
        "initial_fx_date": result.initial_fx_date.isoformat(),
        "final_fx_date": result.final_fx_date.isoformat(),
        "real_usd_return_percentage": result.real_usd_return_percentage,
        "cdi_days_used": result.cdi_days_used,
    }


def _javascript_results(cases: list[dict[str, Any]], dataset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = json.dumps(
        {
            "cases": cases,
            "cdi_rates": dataset["cdi_rates"],
            "usd_rates": dataset["usd_rates"],
        },
        ensure_ascii=True,
    )
    completed = subprocess.run(
        ["node", str(JS_RUNNER_PATH)],
        input=payload,
        text=True,
        capture_output=True,
        check=False,
        cwd=PROJECT_ROOT,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "Falha ao executar comparador JavaScript:\n"
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    raw_results = json.loads(completed.stdout)
    return {item["label"]: item["result"] for item in raw_results}


def _assert_equivalent(
    *,
    label: str,
    python_result: dict[str, Any],
    js_result: dict[str, Any],
    tolerance: float,
) -> list[str]:
    failures: list[str] = []
    for field in FIELDS_TO_COMPARE:
        python_value = python_result[field]
        js_value = js_result[field]
        if isinstance(python_value, float):
            difference = abs(float(python_value) - float(js_value))
            if difference > tolerance:
                failures.append(
                    f"{label}: {field} difere por {difference:.12f} "
                    f"(Python={python_value}, JS={js_value})"
                )
        elif python_value != js_value:
            failures.append(f"{label}: {field} difere (Python={python_value}, JS={js_value})")
    return failures


def main() -> None:
    args = build_parser().parse_args()
    dataset = _load_json(args.dataset)
    validate_static_dataset(dataset)
    cases = _load_json(args.cases)
    if not isinstance(cases, list) or len(cases) < 10:
        raise SystemExit("Informe ao menos 10 periodos de referencia.")

    js_results = _javascript_results(cases, dataset)
    failures: list[str] = []
    for case in cases:
        label = case["label"]
        python_result = _python_result(case, dataset)
        js_result = js_results[label]
        failures.extend(
            _assert_equivalent(
                label=label,
                python_result=python_result,
                js_result=js_result,
                tolerance=args.tolerance,
            )
        )

    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)

    print(f"Validacao cruzada OK: {len(cases)} casos Python vs JavaScript.")


if __name__ == "__main__":
    main()
