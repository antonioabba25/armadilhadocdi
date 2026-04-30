from __future__ import annotations

PAGE_TITLE = "Armadilha do CDI"
PAGE_DESCRIPTION = (
    "Compare o crescimento nominal de aplicacao no CDI em reais com a variacao do dolar "
    "para entender se o CDI realmente valorizou em termos de variacao do USD."
)
DATE_RANGE_CAPTION_TEMPLATE = "Informe datas a partir de {earliest_date}."

START_DATE_LABEL = "Data inicial"
END_DATE_LABEL = "Data final"
INITIAL_BRL_LABEL = "Valor inicial investido (BRL)"
SUBMIT_BUTTON_LABEL = "Analisar periodo"

EMPTY_STATE_MESSAGE = (
    "Preencha o formulario e clique em 'Analisar periodo' para gerar o resultado."
)
LOADING_MESSAGE = "Buscando dados do Banco Central e calculando o resultado..."
UNEXPECTED_ERROR_TEMPLATE = "Ocorreu um erro inesperado: {error}"

SUMMARY_TITLE = "Resumo analitico"
CHART_TITLE = "Grafico comparativo"
CHART_DATA_EXPANDER_LABEL = "Ver base diaria do grafico"
METHODOLOGY_EXPANDER_LABEL = "Metodologia usada"

INTERPRETATION_TIE_TITLE = "O CDI praticamente empatou com a variacao do dolar."
INTERPRETATION_COMPENSATED_TITLE = "A aplicacao no CDI compensou a variacao do dolar."
INTERPRETATION_NOT_COMPENSATED_TITLE = (
    "A aplicacao no CDI nao compensou a variacao do dolar."
)
COMPARISON_EQUAL = "igual a"
COMPARISON_ABOVE = "acima da"
COMPARISON_BELOW = "abaixo da"
INTERPRETATION_DETAILS_TEMPLATE = (
    "No periodo efetivo, o CDI acumulou {cdi_percentage} em reais, "
    "enquanto o USD/BRL variou {usd_variation}. Assim, o CDI ficou "
    "{absolute_gap} {comparison} variacao do dolar. Em equivalente em USD, "
    "o capital saiu de {initial_usd} para {final_usd_with_cdi}, "
    "uma diferenca de {usd_delta} ({real_usd_return})."
)

QUOTE_EXACT_TEMPLATE = "Cotacao {quote_position} encontrada na propria data."
QUOTE_FALLBACK_TEMPLATE = (
    "Cotacao {quote_position} com fallback: {requested_date} -> {effective_date}."
)
QUOTE_POSITION_INITIAL = "inicial"
QUOTE_POSITION_FINAL = "final"
MARKET_PERIOD_EXACT_MESSAGE = "Periodo efetivo de mercado igual ao periodo solicitado."
MARKET_PERIOD_FALLBACK_TEMPLATE = (
    "Periodo efetivo de mercado: {requested_period} -> {effective_period}."
)

METRIC_INITIAL_BRL = "Valor inicial"
METRIC_FINAL_BRL = "Valor final com CDI em BRL"
METRIC_CDI_ACCUMULATED = "CDI acumulado"
METRIC_INITIAL_USD = "USD no inicio"
METRIC_FINAL_USD_WITH_CDI = "USD no fim"
METRIC_USD_BRL_VARIATION = "Variacao USD/BRL"
METRIC_REAL_USD_GAIN = "Valor final com CDI em USD"

TECHNICAL_TABLE_METRIC_COLUMN = "Metrica"
TECHNICAL_TABLE_VALUE_COLUMN = "Valor"
TECHNICAL_TABLE_PERIOD_REQUESTED = "Periodo solicitado"
TECHNICAL_TABLE_EFFECTIVE_MARKET_PERIOD = "Periodo efetivo de mercado"
TECHNICAL_TABLE_INITIAL_USD_BRL = "Cotacao USD/BRL inicial usada"
TECHNICAL_TABLE_FINAL_USD_BRL = "Cotacao USD/BRL final usada"
TECHNICAL_TABLE_USD_BRL_ACCUMULATED_VARIATION = "Variacao acumulada do USD/BRL"
TECHNICAL_TABLE_CDI_VS_USD_BRL = "CDI acima/abaixo do USD/BRL"
TECHNICAL_TABLE_CDI_BUSINESS_DAYS = "Dias uteis de CDI considerados"

CHART_CDI_ACCUMULATED = "CDI Acumulado (%)"
CHART_DATE = "data"
CHART_USD_ACCUMULATED = "USD Acumulado (%)"
CHART_REAL_USD_GAIN = "Ganho Real em USD (%)"
CHART_ADJUSTED_CAPITAL = "Capital Corrigido (BRL)"
CHART_USD_BRL_QUOTE = "Cotacao USD/BRL"

METHODOLOGY_TEXT = """
- O resultado compara o ganho nominal do capital em BRL pelo CDI com a variacao do USD/BRL no mesmo periodo efetivo de mercado.
- O CDI diario vem da serie 12 do SGS/BCB e e acumulado pela regra `data_inicial_efetiva <= data < data_final_efetiva`.
- O USD/BRL usa a cotacao PTAX de venda do Banco Central, obtida pela API Olinda/BCB.
- Calculos, metricas e grafico consideram apenas dias uteis presentes nas series oficiais; fins de semana e feriados nao sao interpolados.
- Datas sem dado oficial sao resolvidas para a ultima data util disponivel. Quando a PTAX nao existe na data efetiva, o app usa a cotacao anterior mais proxima, limitada a 15 dias.
- A diferenca "CDI acima/abaixo do USD/BRL" e medida em pontos percentuais: CDI acumulado menos variacao acumulada do dolar.
- O ganho real em USD mede se o capital corrigido pelo CDI compraria mais ou menos dolares no fim do periodo do que comprava no inicio.
- O calculo nao considera impostos, taxas, spread cambial, IOF, custos operacionais ou diferencas entre PTAX e cotacoes praticadas por uma instituicao.
- Esta analise e uma comparacao historica com dados oficiais; nao e recomendacao de investimento.
"""
