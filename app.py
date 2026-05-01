from __future__ import annotations

import logging
from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st

from armadilha_cdi.config import DEFAULT_CACHE_DIR, EARLIEST_SUPPORTED_DATE
from armadilha_cdi.exceptions import DomainValidationError, MarketDataError
from armadilha_cdi import frontpage_texts as copy
from armadilha_cdi.models import CalculationResult, MarketDataBundle
from armadilha_cdi.services.cache import CacheConfigurationError, build_cache_repository
from armadilha_cdi.services.calculations import (
    BUSINESS_DAYS_PER_MONTH,
    BUSINESS_DAYS_PER_YEAR,
    calculate_equivalent_rate_percentage,
    calculate_result,
)
from armadilha_cdi.services.charts import build_chart_dataframe
from armadilha_cdi.services.data_providers import BCBMarketDataProvider


logger = logging.getLogger(__name__)


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


def equivalent_rate_detail(period_percentage: float, business_days: int) -> str:
    annual_rate = calculate_equivalent_rate_percentage(
        period_percentage,
        business_days,
        BUSINESS_DAYS_PER_YEAR,
    )
    monthly_rate = calculate_equivalent_rate_percentage(
        period_percentage,
        business_days,
        BUSINESS_DAYS_PER_MONTH,
    )
    return copy.METRIC_EQUIVALENT_RATE_TEMPLATE.format(
        annual=format_percent(annual_rate),
        monthly=format_percent(monthly_rate),
    )


def html_escape(value: object) -> str:
    return escape(str(value), quote=True)


def render_frontpage_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;900&family=Space+Grotesk:wght@500;600&display=swap');

        :root {
            color-scheme: light;
            --surface: #faf9f6;
            --surface-lowest: #ffffff;
            --surface-low: #f4f3f1;
            --surface-variant: #e3e2e0;
            --on-surface: #1a1c1a;
            --on-surface-variant: #3f3a2f;
            --outline: #7c7766;
            --outline-variant: #cdc6b3;
            --primary: #5f5200;
            --primary-container: #c5b358;
            --on-primary-container: #403813;
            --secondary: #75584c;
            --tertiary: #50606f;
            --error: #ba1a1a;
            --error-container: #ffdad6;
            --info-container: #d4e4f6;
            --on-info-container: #314150;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: var(--surface);
            color: var(--on-surface);
            font-family: Inter, sans-serif;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1280px;
            padding: 0 32px 64px;
        }

        .cdi-topbar {
            min-height: 64px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid var(--surface-variant);
            margin: 0 -32px;
            padding: 0 32px;
            font-family: "Plus Jakarta Sans", sans-serif;
        }

        .cdi-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            letter-spacing: 0;
            color: var(--on-surface);
        }

        .cdi-brand-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border: 1px solid var(--primary-container);
            color: var(--primary);
            font-size: 12px;
        }

        .cdi-hero {
            position: relative;
            overflow: hidden;
            text-align: center;
            padding: 64px 0 32px;
        }

        .cdi-hero::before {
            content: "";
            position: absolute;
            inset: 10% -12% auto;
            height: 230px;
            opacity: 0.12;
            pointer-events: none;
            background:
                radial-gradient(ellipse at 50% 0%, rgba(197, 179, 88, 0.34), transparent 55%),
                repeating-linear-gradient(164deg, transparent 0 18px, rgba(124, 119, 102, 0.32) 19px, transparent 20px);
            transform: skewY(-7deg);
        }

        .cdi-hero-inner {
            position: relative;
            z-index: 1;
            max-width: 820px;
            margin: 0 auto;
        }

        .cdi-hero h1 {
            margin: 0 0 16px;
            font-family: "Plus Jakarta Sans", sans-serif;
            font-size: clamp(42px, 5vw, 64px);
            line-height: 1.05;
            letter-spacing: 0;
            font-weight: 800;
            color: var(--on-surface);
        }

        .cdi-hero p {
            max-width: 760px;
            margin: 0 auto;
            color: var(--on-surface-variant);
            font-size: 18px;
            line-height: 1.6;
        }

        .cdi-date-note {
            margin-top: 16px;
            color: var(--primary);
            font-family: "Space Grotesk", sans-serif;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        div[data-testid="stForm"] {
            background: var(--surface);
            border: 1px solid var(--outline-variant);
            border-radius: 8px;
            padding: 28px;
            box-shadow: 0 14px 40px rgba(80, 71, 45, 0.06);
            margin-bottom: 32px;
        }

        div[data-testid="stForm"] label p {
            font-family: "Space Grotesk", sans-serif;
            color: var(--on-surface-variant);
            font-size: 12px;
            line-height: 1.2;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        div[data-testid="stForm"] input {
            background: var(--surface-lowest);
            border-color: var(--outline);
            border-radius: 4px;
            color: var(--on-surface);
            font-family: Inter, sans-serif;
        }

        div[data-testid="stDateInput"] input,
        div[data-testid="stNumberInput"] input {
            background-color: var(--surface-lowest);
            color: var(--on-surface);
            caret-color: var(--on-surface);
            border-color: var(--outline);
        }

        div[data-testid="stDateInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 1px var(--primary);
        }

        div[data-testid="stDateInput"] svg,
        div[data-testid="stNumberInput"] svg {
            color: var(--on-surface-variant);
            fill: currentColor;
        }

        div[data-testid="stFormSubmitButton"] button {
            width: 100%;
            min-height: 42px;
            margin-top: 28px;
            border: 1px solid var(--primary-container);
            border-radius: 4px;
            background: var(--primary-container);
            color: var(--on-primary-container);
            font-family: "Space Grotesk", sans-serif;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.03em;
        }

        div[data-testid="stFormSubmitButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:focus {
            border-color: var(--primary);
            background: #d2c365;
            color: var(--on-primary-container);
        }

        .cdi-alert {
            display: flex;
            gap: 16px;
            align-items: flex-start;
            border: 1px solid var(--outline-variant);
            border-radius: 8px;
            padding: 24px;
            background: var(--surface-low);
            margin-bottom: 24px;
        }

        .cdi-alert-positive {
            border-color: var(--primary-container);
        }

        .cdi-alert-negative {
            border-color: var(--error-container);
            background: #fff7f6;
        }

        .cdi-alert-neutral {
            border-color: var(--info-container);
            background: #f6f9fb;
        }

        .cdi-alert-icon {
            margin-top: 3px;
            color: var(--primary);
            font-size: 21px;
            line-height: 1;
        }

        .cdi-alert-negative .cdi-alert-icon {
            color: var(--error);
        }

        .cdi-alert-neutral .cdi-alert-icon {
            color: var(--on-info-container);
        }

        .cdi-alert h2,
        .cdi-panel-heading h2 {
            margin: 0 0 4px;
            font-family: "Plus Jakarta Sans", sans-serif;
            color: var(--on-surface);
            font-size: 24px;
            line-height: 1.3;
            font-weight: 700;
            letter-spacing: 0;
        }

        .cdi-alert p {
            margin: 0;
            color: var(--on-surface-variant);
            font-size: 16px;
            line-height: 1.5;
        }

        .cdi-metric-card {
            min-height: 132px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: var(--surface);
            border: 1px solid var(--outline-variant);
            border-radius: 8px;
            padding: 24px;
        }

        .cdi-metric-card-highlight {
            background: rgba(218, 199, 105, 0.18);
            border-color: var(--primary-container);
        }

        .cdi-metric-label {
            margin-bottom: 14px;
            font-family: "Space Grotesk", sans-serif;
            color: var(--on-surface-variant);
            font-size: 12px;
            line-height: 1.2;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .cdi-metric-value {
            font-family: "Plus Jakarta Sans", sans-serif;
            color: var(--on-surface);
            font-size: clamp(24px, 2.3vw, 32px);
            line-height: 1.15;
            letter-spacing: 0;
            font-weight: 800;
            word-break: break-word;
        }

        .cdi-metric-value-positive,
        .cdi-metric-card-highlight .cdi-metric-value {
            color: var(--primary);
        }

        .cdi-metric-value-negative {
            color: var(--error);
        }

        .cdi-metric-detail {
            margin-top: 8px;
            color: var(--on-surface-variant);
            font-size: 13px;
            line-height: 1.35;
            white-space: pre-line;
        }

        .cdi-notes {
            display: grid;
            gap: 8px;
            margin: 8px 0 32px;
        }

        .cdi-note {
            color: var(--on-surface-variant);
            font-size: 13px;
            line-height: 1.4;
        }

        .cdi-panel {
            background: var(--surface);
            border: 1px solid var(--outline-variant);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 8px;
        }

        .cdi-panel-heading {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }

        .cdi-panel-heading h2 {
            margin: 0;
        }

        .cdi-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            justify-content: flex-end;
            color: var(--on-surface-variant);
            font-family: "Space Grotesk", sans-serif;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.03em;
        }

        .cdi-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 7px;
        }

        .cdi-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
        }

        .cdi-dot-cdi { background: var(--primary); }
        .cdi-dot-usd { background: var(--secondary); }
        .cdi-dot-real { background: var(--tertiary); }

        .cdi-table-wrap {
            overflow-x: auto;
            border: 1px solid var(--outline-variant);
            border-radius: 8px;
            background: var(--surface);
            margin: 32px 0;
        }

        .cdi-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 15px;
            line-height: 1.45;
        }

        .cdi-table thead {
            background: var(--surface-low);
        }

        .cdi-table th {
            padding: 14px 16px;
            text-align: left;
            color: var(--on-surface-variant);
            font-family: "Space Grotesk", sans-serif;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            border-bottom: 1px solid var(--outline-variant);
        }

        .cdi-table td {
            padding: 16px;
            color: var(--on-surface);
            border-bottom: 1px solid rgba(205, 198, 179, 0.8);
        }

        .cdi-table tbody tr:last-child td {
            border-bottom: 0;
        }

        div[data-testid="stExpander"] {
            border-color: var(--outline-variant);
            border-radius: 8px;
            background: var(--surface);
            color: var(--on-surface);
        }

        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary {
            background: var(--surface);
            color: var(--on-surface);
        }

        div[data-testid="stExpander"] summary:hover {
            background: var(--surface-low);
        }

        div[data-testid="stExpander"] summary p {
            font-family: "Space Grotesk", sans-serif;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.03em;
            color: var(--on-surface);
            text-transform: uppercase;
        }

        div[data-testid="stExpander"] summary svg {
            color: var(--on-surface);
            fill: currentColor;
        }

        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"],
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
            color: var(--on-surface);
        }

        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] code {
            background: #ece7d8;
            border: 1px solid var(--outline-variant);
            border-radius: 4px;
            color: var(--on-surface);
            padding: 1px 4px;
        }

        .cdi-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 24px;
            border-top: 1px solid var(--surface-variant);
            margin: 56px -32px 0;
            padding: 32px;
            color: var(--on-surface-variant);
            font-family: "Plus Jakarta Sans", sans-serif;
            font-size: 11px;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .cdi-footer strong {
            color: var(--on-surface);
            white-space: nowrap;
        }

        .cdi-footer-note {
            max-width: 680px;
            margin: 0;
            text-align: right;
            line-height: 1.5;
        }

        @media (max-width: 760px) {
            .block-container {
                padding: 0 16px 40px;
            }

            .cdi-topbar {
                margin: 0 -16px;
                padding: 0 16px;
            }

            .cdi-hero {
                padding: 40px 0 24px;
            }

            .cdi-hero h1 {
                font-size: 34px;
                line-height: 1.08;
            }

            .cdi-hero p {
                font-size: 14px;
                line-height: 1.55;
            }

            div[data-testid="stForm"] {
                padding: 18px;
            }

            div[data-testid="stFormSubmitButton"] button {
                margin-top: 8px;
            }

            .cdi-alert,
            .cdi-metric-card,
            .cdi-panel {
                padding: 18px;
            }

            .cdi-panel-heading,
            .cdi-footer {
                align-items: flex-start;
                flex-direction: column;
            }

            .cdi-legend {
                justify-content: flex-start;
            }

            .cdi-footer {
                margin-left: -16px;
                margin-right: -16px;
                padding: 28px 16px;
            }

            .cdi-footer strong {
                white-space: normal;
            }

            .cdi-footer-note {
                text-align: left;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_bar() -> None:
    st.markdown(
        """
        <header class="cdi-topbar">
            <div class="cdi-brand">
                <span class="cdi-brand-mark">∿</span>
                <span>Armadilha do CDI</span>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    date_note = copy.DATE_RANGE_CAPTION_TEMPLATE.format(
        earliest_date=EARLIEST_SUPPORTED_DATE.strftime("%d/%m/%Y")
    )
    st.markdown(
        f"""
        <section class="cdi-hero">
            <div class="cdi-hero-inner">
                <h1>O CDI venceu o Dólar? Descubra em segundos.</h1>
                <p>{html_escape(copy.PAGE_DESCRIPTION)}</p>
                <div class="cdi-date-note">{html_escape(date_note)}</div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
        <footer class="cdi-footer">
            <strong>{html_escape(copy.FOOTER_BRAND)}</strong>
            <p class="cdi-footer-note">{html_escape(copy.FOOTER_NOTE)}</p>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def render_status_message(message: str, status: str = "neutral") -> None:
    icon = {"positive": "✓", "negative": "!", "neutral": "i"}.get(status, "i")
    st.markdown(
        f"""
        <div class="cdi-alert cdi-alert-{html_escape(status)}">
            <div class="cdi-alert-icon">{html_escape(icon)}</div>
            <div><h2>{html_escape(message)}</h2></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    title: str,
    value: str,
    detail: str = "",
    *,
    highlight: bool = False,
    tone: str = "",
) -> None:
    highlight_class = " cdi-metric-card-highlight" if highlight else ""
    tone_class = f" cdi-metric-value-{tone}" if tone else ""
    metric_body = (
        f'<div class="cdi-metric-value{tone_class}">{html_escape(value)}</div>'
    )
    if detail:
        metric_body += f'<div class="cdi-metric-detail">{html_escape(detail)}</div>'

    st.markdown(
        (
            f'<div class="cdi-metric-card{highlight_class}">'
            f'<div class="cdi-metric-label">{html_escape(title)}</div>'
            f"<div>{metric_body}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


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
    return copy.QUOTE_PREVIOUS_DATE_TEMPLATE.format(
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
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric_card(copy.METRIC_INITIAL_BRL, format_brl(result.initial_brl))
    with col2:
        render_metric_card(
            copy.METRIC_FINAL_BRL,
            format_brl(result.final_brl),
            detail=f"{format_percent(result.cdi_percentage)} nominal",
        )
    with col3:
        render_metric_card(
            copy.METRIC_CDI_ACCUMULATED,
            format_percent(result.cdi_percentage),
            detail=equivalent_rate_detail(result.cdi_percentage, result.cdi_days_used),
            highlight=True,
            tone="positive",
        )

    usd_variation = usd_variation_percentage(result)
    real_usd_tone = "positive" if result.real_usd_return_percentage >= 0 else "negative"
    usd_variation_tone = "negative" if usd_variation > result.cdi_percentage else ""

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        render_metric_card(
            copy.METRIC_INITIAL_USD,
            format_usd(result.initial_usd),
            detail=f"PTAX {result.initial_usdbrl:,.4f}",
        )
    with col5:
        render_metric_card(
            copy.METRIC_FINAL_USD_WITH_CDI,
            format_usd(result.final_usd_with_cdi),
            detail=f"Variacao % em USD {format_percent(result.real_usd_return_percentage)}",
            highlight=True,
            tone=real_usd_tone,
        )
    with col6:
        render_metric_card(
            copy.METRIC_USD_BRL_VARIATION,
            format_percent(usd_variation),
            detail=(
                f"{equivalent_rate_detail(usd_variation, result.cdi_days_used)}\n"
                f"{result.initial_usdbrl:,.4f} -> {result.final_usdbrl:,.4f}"
            ),
            tone=usd_variation_tone,
        )
    with col7:
        render_metric_card(
            copy.METRIC_USD_PERCENT_VARIATION,
            format_percent(result.real_usd_return_percentage),
            detail=equivalent_rate_detail(
                result.real_usd_return_percentage,
                result.cdi_days_used,
            ),
            tone=real_usd_tone,
        )

    render_notes(result)


def render_notes(result: CalculationResult) -> None:
    notes = [
        quote_note(result, copy.QUOTE_POSITION_INITIAL),
        quote_note(result, copy.QUOTE_POSITION_FINAL),
        market_period_note(result),
    ]
    notes_html = "".join(
        f'<div class="cdi-note">{html_escape(note)}</div>' for note in notes
    )
    st.markdown(f'<div class="cdi-notes">{notes_html}</div>', unsafe_allow_html=True)


def technical_table_dataframe(result: CalculationResult) -> pd.DataFrame:
    return pd.DataFrame(
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
    )


def render_technical_table(result: CalculationResult) -> None:
    dataframe = technical_table_dataframe(result)
    header_html = "".join(
        f"<th>{html_escape(column)}</th>" for column in dataframe.columns
    )
    rows_html = ""
    for _, row in dataframe.iterrows():
        rows_html += "<tr>" + "".join(
            f"<td>{html_escape(row[column])}</td>" for column in dataframe.columns
        ) + "</tr>"

    st.markdown(
        f"""
        <div class="cdi-table-wrap">
            <table class="cdi-table">
                <thead><tr>{header_html}</tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_long_dataframe(chart_df: pd.DataFrame) -> pd.DataFrame:
    visible_columns = [
        copy.CHART_CDI_ACCUMULATED,
        copy.CHART_USD_ACCUMULATED,
        copy.CHART_USD_PERCENT_VARIATION,
    ]
    plot_df = chart_df[[copy.CHART_DATE, *visible_columns]].copy()
    plot_df[copy.CHART_DATE] = pd.to_datetime(plot_df[copy.CHART_DATE])
    return plot_df.melt(
        id_vars=copy.CHART_DATE,
        value_vars=visible_columns,
        var_name="Serie",
        value_name="Percentual",
    )


def render_chart_panel(chart_df: pd.DataFrame) -> None:
    st.markdown(
        f"""
        <div class="cdi-panel">
            <div class="cdi-panel-heading">
                <h2>{html_escape(copy.CHART_TITLE)}</h2>
                <div class="cdi-legend">
                    <span class="cdi-legend-item"><span class="cdi-dot cdi-dot-cdi"></span>CDI</span>
                    <span class="cdi-legend-item"><span class="cdi-dot cdi-dot-usd"></span>USD/BRL</span>
                    <span class="cdi-legend-item"><span class="cdi-dot cdi-dot-real"></span>Variacao % em USD</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.vega_lite_chart(
        chart_long_dataframe(chart_df),
        {
            "height": 380,
            "mark": {"type": "line", "strokeWidth": 2.5, "interpolate": "monotone"},
            "encoding": {
                "x": {
                    "field": copy.CHART_DATE,
                    "type": "temporal",
                    "title": None,
                    "axis": {
                        "labelColor": "#4b4738",
                        "tickColor": "#cdc6b3",
                        "gridColor": "#efeeeb",
                    },
                },
                "y": {
                    "field": "Percentual",
                    "type": "quantitative",
                    "title": "Acumulado (%)",
                    "axis": {
                        "labelColor": "#4b4738",
                        "titleColor": "#4b4738",
                        "tickColor": "#cdc6b3",
                        "gridColor": "#e9e8e5",
                    },
                },
                "color": {
                    "field": "Serie",
                    "type": "nominal",
                    "scale": {
                        "domain": [
                            copy.CHART_CDI_ACCUMULATED,
                            copy.CHART_USD_ACCUMULATED,
                            copy.CHART_USD_PERCENT_VARIATION,
                        ],
                        "range": ["#6c5e06", "#75584c", "#50606f"],
                    },
                    "legend": None,
                },
                "tooltip": [
                    {"field": copy.CHART_DATE, "type": "temporal", "title": "Data"},
                    {"field": "Serie", "type": "nominal", "title": "Série"},
                    {
                        "field": "Percentual",
                        "type": "quantitative",
                        "title": "Acumulado (%)",
                        "format": ".2f",
                    },
                ],
            },
            "config": {
                "background": "#faf9f6",
                "view": {"stroke": "#cdc6b3"},
                "font": "Inter",
            },
        },
        width="stretch",
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

    render_chart_panel(chart_df)

    with st.expander(copy.CHART_DATA_EXPANDER_LABEL):
        st.dataframe(chart_df, width="stretch", hide_index=True)


def main() -> None:
    st.set_page_config(page_title=copy.PAGE_TITLE, layout="wide")
    render_frontpage_styles()
    render_top_bar()
    render_hero()

    today = date.today()
    default_end = today
    default_start = today - timedelta(days=365)

    with st.form("analise_form"):
        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.78])
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
        with col4:
            submitted = st.form_submit_button(copy.SUBMIT_BUTTON_LABEL)

    if not submitted:
        render_status_message(copy.EMPTY_STATE_MESSAGE, "neutral")
        render_footer()
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
        render_technical_table(result)

        with st.expander(copy.METHODOLOGY_EXPANDER_LABEL):
            st.markdown('<div id="metodologia"></div>', unsafe_allow_html=True)
            st.markdown(copy.METHODOLOGY_TEXT)
        render_footer()

    except (DomainValidationError, MarketDataError, CacheConfigurationError) as exc:
        render_status_message(str(exc), "negative")
        render_footer()
    except Exception:  # pragma: no cover - safeguard for UI
        logger.exception("Erro inesperado ao renderizar a aplicacao.")
        render_status_message(copy.UNEXPECTED_ERROR_MESSAGE, "negative")
        render_footer()


if __name__ == "__main__":
    main()
