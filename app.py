from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from armadilha_cdi.config import DEFAULT_CACHE_DIR, EARLIEST_SUPPORTED_DATE
from armadilha_cdi.exceptions import DomainValidationError, MarketDataError
from armadilha_cdi import frontpage_texts as copy
from armadilha_cdi.models import CalculationResult, MarketDataBundle
from armadilha_cdi.services.cache import CacheConfigurationError, build_cache_repository
from armadilha_cdi.services.calculations import calculate_result
from armadilha_cdi.services.charts import build_chart_dataframe
from armadilha_cdi.services.data_providers import BCBMarketDataProvider


@st.cache_resource
def get_market_data_provider() -> BCBMarketDataProvider:
    """Build a single provider instance for the Streamlit process."""
    return BCBMarketDataProvider(
        cache_repository=build_cache_repository(
            cache_dir=DEFAULT_CACHE_DIR,
            backend=get_streamlit_secret("MARKET_DATA_CACHE_BACKEND"),
            database_url=(
                get_streamlit_secret("SUPABASE_DATABASE_URL")
                or get_streamlit_secret("DATABASE_URL")
            ),
            table_name=get_streamlit_secret("SUPABASE_CACHE_TABLE"),
        )
    )


def get_streamlit_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except (AttributeError, FileNotFoundError, KeyError):
        return None

    if value is None:
        return None
    value = str(value).strip()
    return value or None


def format_brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_usd(value: float) -> str:
    return f"US$ {value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage_points(value: float) -> str:
    return f"{value:,.2f} p.p.".replace(",", "X").replace(".", ",").replace("X", ".")


def usd_variation_percentage(result: CalculationResult) -> float:
    return ((result.final_usdbrl / result.initial_usdbrl) - 1) * 100


def cdi_vs_usd_gap_percentage_points(result: CalculationResult) -> float:
    return result.cdi_percentage - usd_variation_percentage(result)


def result_interpretation(result: CalculationResult) -> tuple[str, str]:
    usd_variation = usd_variation_percentage(result)
    gap = cdi_vs_usd_gap_percentage_points(result)
    absolute_gap = abs(gap)
    usd_delta = result.final_usd_with_cdi - result.initial_usd

    if abs(gap) < 0.005:
        title = copy.INTERPRETATION_TIE_TITLE
        comparison = copy.COMPARISON_EQUAL
    elif gap > 0:
        title = copy.INTERPRETATION_COMPENSATED_TITLE
        comparison = copy.COMPARISON_ABOVE
    else:
        title = copy.INTERPRETATION_NOT_COMPENSATED_TITLE
        comparison = copy.COMPARISON_BELOW

    details = copy.INTERPRETATION_DETAILS_TEMPLATE.format(
        cdi_percentage=format_percent(result.cdi_percentage),
        usd_variation=format_percent(usd_variation),
        absolute_gap=format_percentage_points(absolute_gap),
        comparison=comparison,
        initial_usd=format_usd(result.initial_usd),
        final_usd_with_cdi=format_usd(result.final_usd_with_cdi),
        usd_delta=format_usd(usd_delta),
        real_usd_return=format_percent(result.real_usd_return_percentage),
    )
    return title, details


def quote_note(result: CalculationResult, quote_position: str) -> str:
    requested = (
        result.start_date
        if quote_position == copy.QUOTE_POSITION_INITIAL
        else result.end_date
    )
    effective = (
        result.initial_fx_date
        if quote_position == copy.QUOTE_POSITION_INITIAL
        else result.final_fx_date
    )
    if requested == effective:
        return copy.QUOTE_EXACT_TEMPLATE.format(quote_position=quote_position)
    return copy.QUOTE_FALLBACK_TEMPLATE.format(
        quote_position=quote_position,
        requested_date=requested.strftime("%d/%m/%Y"),
        effective_date=effective.strftime("%d/%m/%Y"),
    )


def market_period_note(result: CalculationResult) -> str:
    if (
        result.start_date == result.effective_start_date
        and result.end_date == result.effective_end_date
    ):
        return copy.MARKET_PERIOD_EXACT_MESSAGE

    return copy.MARKET_PERIOD_FALLBACK_TEMPLATE.format(
        requested_period=result.period_label,
        effective_period=result.effective_period_label,
    )


def render_summary(result: CalculationResult) -> None:
    st.subheader(copy.SUMMARY_TITLE)
    title, details = result_interpretation(result)
    gap = cdi_vs_usd_gap_percentage_points(result)

    if gap > 0.005:
        st.success(f"**{title}** {details}")
    elif gap < -0.005:
        st.error(f"**{title}** {details}")
    else:
        st.info(f"**{title}** {details}")

    col1, col2, col3 = st.columns(3)
    col1.metric(copy.METRIC_INITIAL_BRL, format_brl(result.initial_brl))
    col2.metric(copy.METRIC_FINAL_BRL, format_brl(result.final_brl))
    col3.metric(copy.METRIC_CDI_ACCUMULATED, format_percent(result.cdi_percentage))

    col4, col5, col6, col7 = st.columns(4)
    col4.metric(copy.METRIC_INITIAL_USD, format_usd(result.initial_usd))
    col5.metric(copy.METRIC_FINAL_USD_WITH_CDI, format_usd(result.final_usd_with_cdi))
    col6.metric(
        copy.METRIC_USD_BRL_VARIATION,
        format_percent(usd_variation_percentage(result)),
    )
    col7.metric(
        copy.METRIC_REAL_USD_GAIN,
        format_percent(result.real_usd_return_percentage),
    )

    st.caption(quote_note(result, copy.QUOTE_POSITION_INITIAL))
    st.caption(quote_note(result, copy.QUOTE_POSITION_FINAL))
    st.caption(market_period_note(result))

    st.dataframe(
        pd.DataFrame(
            {
                copy.TECHNICAL_TABLE_METRIC_COLUMN: [
                    copy.TECHNICAL_TABLE_PERIOD_REQUESTED,
                    copy.TECHNICAL_TABLE_EFFECTIVE_MARKET_PERIOD,
                    copy.TECHNICAL_TABLE_INITIAL_USD_BRL,
                    copy.TECHNICAL_TABLE_FINAL_USD_BRL,
                    copy.TECHNICAL_TABLE_USD_BRL_ACCUMULATED_VARIATION,
                    copy.TECHNICAL_TABLE_CDI_VS_USD_BRL,
                    copy.TECHNICAL_TABLE_CDI_BUSINESS_DAYS,
                ],
                copy.TECHNICAL_TABLE_VALUE_COLUMN: [
                    result.period_label,
                    result.effective_period_label,
                    f"{result.initial_usdbrl:,.4f}",
                    f"{result.final_usdbrl:,.4f}",
                    format_percent(usd_variation_percentage(result)),
                    format_percentage_points(cdi_vs_usd_gap_percentage_points(result)),
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

    st.subheader(copy.CHART_TITLE)
    st.line_chart(
        chart_df.set_index(copy.CHART_DATE)[
            [
                copy.CHART_CDI_ACCUMULATED,
                copy.CHART_USD_ACCUMULATED,
                copy.CHART_REAL_USD_GAIN,
            ]
        ],
        use_container_width=True,
    )

    with st.expander(copy.CHART_DATA_EXPANDER_LABEL):
        st.dataframe(chart_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title=copy.PAGE_TITLE, layout="wide")
    st.title(copy.PAGE_TITLE)
    st.write(copy.PAGE_DESCRIPTION)

    today = date.today()
    default_end = today
    default_start = today - timedelta(days=365)

    st.caption(
        copy.DATE_RANGE_CAPTION_TEMPLATE.format(
            earliest_date=EARLIEST_SUPPORTED_DATE.strftime("%d/%m/%Y")
        )
    )

    with st.form("analise_form"):
        col1, col2, col3 = st.columns(3)
        start_date = col1.date_input(
            copy.START_DATE_LABEL,
            value=default_start,
            min_value=EARLIEST_SUPPORTED_DATE,
            max_value=today,
            format="DD/MM/YYYY",
        )
        end_date = col2.date_input(
            copy.END_DATE_LABEL,
            value=default_end,
            min_value=EARLIEST_SUPPORTED_DATE,
            max_value=today,
            format="DD/MM/YYYY",
        )
        initial_brl = col3.number_input(
            copy.INITIAL_BRL_LABEL,
            min_value=0.01,
            value=10000.00,
            step=100.00,
            format="%.2f",
        )
        submitted = st.form_submit_button(copy.SUBMIT_BUTTON_LABEL)

    if not submitted:
        st.info(copy.EMPTY_STATE_MESSAGE)
        return

    try:
        with st.spinner(copy.LOADING_MESSAGE):
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

        with st.expander(copy.METHODOLOGY_EXPANDER_LABEL):
            st.markdown(copy.METHODOLOGY_TEXT)

    except (DomainValidationError, MarketDataError, CacheConfigurationError) as exc:
        st.error(str(exc))
    except Exception as exc:  # pragma: no cover - safeguard for UI
        st.error(copy.UNEXPECTED_ERROR_TEMPLATE.format(error=exc))


if __name__ == "__main__":
    main()
