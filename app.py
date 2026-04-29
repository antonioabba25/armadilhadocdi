from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from armadilha_cdi.config import DEFAULT_CACHE_DIR, EARLIEST_SUPPORTED_DATE
from armadilha_cdi.exceptions import DomainValidationError, MarketDataError
from armadilha_cdi.models import CalculationResult, MarketDataBundle
from armadilha_cdi.services.cache import JsonFileCache
from armadilha_cdi.services.calculations import calculate_result
from armadilha_cdi.services.charts import build_chart_dataframe
from armadilha_cdi.services.data_providers import BCBMarketDataProvider


@st.cache_resource
def get_market_data_provider() -> BCBMarketDataProvider:
    """Build a single provider instance for the Streamlit process."""
    return BCBMarketDataProvider(cache_repository=JsonFileCache(DEFAULT_CACHE_DIR))


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_usd(value: float) -> str:
    return f"US$ {value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def quote_note(result: CalculationResult, quote_position: str) -> str:
    requested = result.start_date if quote_position == "inicial" else result.end_date
    effective = result.initial_fx_date if quote_position == "inicial" else result.final_fx_date
    if requested == effective:
        return f"Cotacao {quote_position} encontrada na propria data."
    return (
        f"Cotacao {quote_position} com fallback: "
        f"{requested.strftime('%d/%m/%Y')} -> {effective.strftime('%d/%m/%Y')}."
    )


def market_period_note(result: CalculationResult) -> str:
    if (
        result.start_date == result.effective_start_date
        and result.end_date == result.effective_end_date
    ):
        return "Periodo efetivo de mercado igual ao periodo solicitado."

    return (
        "Periodo efetivo de mercado: "
        f"{result.period_label} -> {result.effective_period_label}."
    )


def render_summary(result: CalculationResult) -> None:
    st.subheader("Resumo analitico")

    col1, col2, col3 = st.columns(3)
    col1.metric("Valor inicial", format_brl(result.initial_brl))
    col2.metric("Valor final com CDI", format_brl(result.final_brl))
    col3.metric("CDI acumulado", format_percent(result.cdi_percentage))

    col4, col5, col6 = st.columns(3)
    col4.metric("USD no inicio", format_usd(result.initial_usd))
    col5.metric("USD no fim com CDI", format_usd(result.final_usd_with_cdi))
    col6.metric("Ganho real em USD", format_percent(result.real_usd_return_percentage))

    st.caption(quote_note(result, "inicial"))
    st.caption(quote_note(result, "final"))
    st.caption(market_period_note(result))

    st.dataframe(
        pd.DataFrame(
            {
                "Metrica": [
                    "Periodo solicitado",
                    "Periodo efetivo de mercado",
                    "Cotacao USD/BRL inicial usada",
                    "Cotacao USD/BRL final usada",
                    "Dias uteis de CDI considerados",
                ],
                "Valor": [
                    result.period_label,
                    result.effective_period_label,
                    f"{result.initial_usdbrl:,.4f}",
                    f"{result.final_usdbrl:,.4f}",
                    str(result.cdi_days_used),
                ],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_chart(
    start_date: date,
    end_date: date,
    initial_brl: float,
    market_data: MarketDataBundle,
) -> None:
    chart_df = build_chart_dataframe(
        start_date=start_date,
        end_date=end_date,
        cdi_rates=market_data.cdi_rates,
        usd_rates=market_data.usd_rates,
        initial_brl=initial_brl,
    )

    st.subheader("Grafico comparativo")
    st.line_chart(
        chart_df.set_index("data")[
            [
                "CDI Acumulado (%)",
                "USD Acumulado (%)",
                "Ganho Real em USD (%)",
            ]
        ],
        use_container_width=True,
    )

    with st.expander("Ver base diaria do grafico"):
        st.dataframe(chart_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Armadilha do CDI", layout="wide")
    st.title("Armadilha do CDI")
    st.write(
        "Compare o crescimento nominal em reais com a variacao do dolar "
        "para entender se o CDI realmente preservou seu poder relativo em USD."
    )

    today = date.today()
    default_end = today
    default_start = today - timedelta(days=365)

    st.caption(
        "Informe datas a partir de "
        f"{EARLIEST_SUPPORTED_DATE.strftime('%d/%m/%Y')}."
    )

    with st.form("analise_form"):
        col1, col2, col3 = st.columns(3)
        start_date = col1.date_input(
            "Data inicial",
            value=default_start,
            min_value=EARLIEST_SUPPORTED_DATE,
            max_value=today,
            format="DD/MM/YYYY",
        )
        end_date = col2.date_input(
            "Data final",
            value=default_end,
            min_value=EARLIEST_SUPPORTED_DATE,
            max_value=today,
            format="DD/MM/YYYY",
        )
        initial_brl = col3.number_input(
            "Valor inicial investido (BRL)",
            min_value=0.01,
            value=10000.00,
            step=100.00,
            format="%.2f",
        )
        submitted = st.form_submit_button("Analisar periodo")

    if not submitted:
        st.info("Preencha o formulario e clique em 'Analisar periodo' para gerar o resultado.")
        return

    try:
        with st.spinner("Buscando dados do Banco Central e calculando o resultado..."):
            provider = get_market_data_provider()
            market_data = provider.get_market_data(start_date=start_date, end_date=end_date)
            result = calculate_result(
                start_date=start_date,
                end_date=end_date,
                initial_brl=initial_brl,
                cdi_rates=market_data.cdi_rates,
                usd_rates=market_data.usd_rates,
            )

        render_summary(result)
        render_chart(
            start_date=start_date,
            end_date=end_date,
            initial_brl=initial_brl,
            market_data=market_data,
        )

        with st.expander("Metodologia usada"):
            st.markdown(
                """
                - Datas sem dado oficial sao resolvidas para o ultimo dia util disponivel.
                - O CDI e acumulado pela regra `data_inicial_efetiva <= data < data_final_efetiva`.
                - O dolar usa a cotacao PTAX de venda do Banco Central.
                - Se nao houver cotacao na data exata, o app busca a ultima cotacao anterior em ate 15 dias.
                - O grafico considera apenas dias uteis presentes nas series oficiais.
                - O ganho real em USD mede a variacao do capital corrigido pelo CDI quando convertido para dolar no fim do periodo.
                """
            )

    except (DomainValidationError, MarketDataError) as exc:
        st.error(str(exc))
    except Exception as exc:  # pragma: no cover - safeguard for UI
        st.error(f"Ocorreu um erro inesperado: {exc}")


if __name__ == "__main__":
    main()
