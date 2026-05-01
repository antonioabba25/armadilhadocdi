from __future__ import annotations

PAGE_TITLE = "Armadilha do CDI"
PAGE_DESCRIPTION = (
    "Compare o crescimento nominal de aplicação no CDI em reais com a variação do dólar "
    "para entender se o CDI realmente valorizou em termos de variação do USD."
)
DATE_RANGE_CAPTION_TEMPLATE = "Informe datas a partir de {earliest_date}."

START_DATE_LABEL = "Data inicial"
END_DATE_LABEL = "Data final"
INITIAL_BRL_LABEL = "Valor inicial investido (BRL)"
SUBMIT_BUTTON_LABEL = "Analisar período"
FOOTER_BRAND = "Armadilha do CDI"
FOOTER_NOTE = (
    "CDI SGS/BCB série 12 e USD/BRL PTAX venda. Comparação histórica, sem "
    "impostos, taxas ou recomendação de investimento."
)

EMPTY_STATE_MESSAGE = (
    "Preencha o formulario e clique em 'Analisar período' para gerar o resultado."
)
LOADING_MESSAGE = "Buscando dados do Banco Central e calculando o resultado..."
UNEXPECTED_ERROR_MESSAGE = (
    "Ocorreu um erro inesperado. Tente novamente em instantes."
)

CHART_TITLE = "Gráfico comparativo"
CHART_DATA_EXPANDER_LABEL = "Ver base diária do gráfico"
METHODOLOGY_EXPANDER_LABEL = "Metodologia usada"

QUOTE_EXACT_TEMPLATE = "Cotação {quote_position} encontrada na própria data."
QUOTE_PREVIOUS_DATE_TEMPLATE = (
    "Cotação {quote_position}: usada a última PTAX oficial anterior "
    "({requested_date} -> {effective_date})."
)
QUOTE_POSITION_INITIAL = "inicial"
QUOTE_POSITION_FINAL = "final"
MARKET_PERIOD_EXACT_MESSAGE = "Período efetivo de mercado igual ao período solicitado."
MARKET_PERIOD_FALLBACK_TEMPLATE = (
    "Período efetivo de mercado: {requested_period} -> {effective_period}."
)

METRIC_INITIAL_BRL = "Valor inicial - em BRL"
METRIC_FINAL_BRL = "Valor final com CDI - em BRL"
METRIC_CDI_ACCUMULATED = "CDI acumulado - em BRL"
METRIC_INITIAL_USD = "Valor inicial - em USD"
METRIC_FINAL_USD_WITH_CDI = "Valor final com CDI - em USD"
METRIC_USD_BRL_VARIATION = "Variação USD/BRL"
METRIC_USD_PERCENT_VARIATION = "Variação % em USD"
METRIC_EQUIVALENT_RATE_TEMPLATE = "Equiv.: {annual} a.a. | {monthly} a.m."

TECHNICAL_TABLE_METRIC_COLUMN = "Métrica"
TECHNICAL_TABLE_VALUE_COLUMN = "Valor"
TECHNICAL_TABLE_PERIOD_REQUESTED = "Período solicitado"
TECHNICAL_TABLE_EFFECTIVE_MARKET_PERIOD = "Período efetivo de mercado"
TECHNICAL_TABLE_INITIAL_USD_BRL = "Cotação USD/BRL inicial usada"
TECHNICAL_TABLE_FINAL_USD_BRL = "Cotação USD/BRL final usada"
TECHNICAL_TABLE_USD_BRL_ACCUMULATED_VARIATION = "Variação acumulada do USD/BRL"
TECHNICAL_TABLE_CDI_VS_USD_BRL = "CDI acima/abaixo do USD/BRL"
TECHNICAL_TABLE_CDI_BUSINESS_DAYS = "Dias úteis de CDI considerados"

CHART_CDI_ACCUMULATED = "CDI Acumulado (%)"
CHART_DATE = "data"
CHART_USD_ACCUMULATED = "USD/BRL Acumulado (%)"
CHART_USD_PERCENT_VARIATION = "Variação % em USD"
CHART_ADJUSTED_CAPITAL = "Capital Corrigido (BRL)"
CHART_USD_BRL_QUOTE = "Cotação USD/BRL"

METHODOLOGY_TEXT = """
- O resultado compara o ganho nominal do capital em BRL pelo CDI com a variação do USD/BRL no mesmo período efetivo de mercado.
- O CDI diário vem da serie 12 do SGS/BCB e é acumulado pela regra `data_inicial_efetiva <= data < data_final_efetiva`.
- O USD/BRL usa a cotação PTAX de venda do Banco Central, obtida pela API Olinda/BCB.
- Cálculos, métricas e gráfico consideram apenas dias úteis presentes nas séries oficiais; fins de semana e feriados não são interpolados.
- Datas sem dado oficial são resolvidas para a última data útil disponível. Quando a PTAX não existe na data efetiva, o app usa a cotação anterior mais próxima, limitada a 15 dias.
- A diferença "CDI acima/abaixo do USD/BRL" é medida em pontos percentuais: CDI acumulado menos variação acumulada do dólar.
- A variação em USD mede se o capital corrigido pelo CDI compraria mais ou menos dólares no fim do período do que comprava no início.
- As taxas equivalentes anual e mensal são periodizações matemáticas do percentual observado, usando 252 e 22 dias úteis, e não representam previsão.
- O cálculo não considera impostos, taxas, spread cambial, IOF, custos operacionais ou diferenças entre PTAX e cotações praticadas por uma instituição.
- Esta análise e uma comparação histórica com dados oficiais; não é recomendação de investimento.
"""
