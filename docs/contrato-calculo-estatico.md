# Contrato de Calculo da Versao Estatica

Este contrato congela o comportamento que a publicacao estatica deve reproduzir antes de virar a superficie publica principal. A referencia inicial continua sendo o nucleo Python em `armadilha_cdi/services/calculations.py`.

## Pergunta do Produto

A aplicacao responde se um capital aplicado em CDI entre duas datas melhorou, piorou ou apenas pareceu melhorar quando medido em USD. A metrica central e `real_usd_return_percentage`.

## Entradas

- `start_date`: data inicial solicitada, em `YYYY-MM-DD`, igual ou posterior a `1994-07-01`.
- `end_date`: data final solicitada, em `YYYY-MM-DD`, maior que `start_date`.
- `initial_brl`: valor inicial investido em BRL, maior que zero.
- `cdi_rates`: mapa `{YYYY-MM-DD: taxa_diaria_percentual}` da serie 12 SGS/BCB.
- `usd_rates`: mapa `{YYYY-MM-DD: cotacao_venda}` da PTAX USD/BRL.

## Saidas Equivalentes a `CalculationResult`

- `start_date`
- `end_date`
- `effective_start_date`
- `effective_end_date`
- `initial_brl`
- `final_brl`
- `cdi_factor`
- `cdi_percentage`
- `initial_usd`
- `final_usd_with_cdi`
- `initial_usdbrl`
- `final_usdbrl`
- `initial_fx_date`
- `final_fx_date`
- `real_usd_return_percentage`
- `cdi_days_used`

## Regras Obrigatorias

- A data inicial deve ser `1994-07-01` ou posterior.
- Datas sem dado oficial de mercado sao resolvidas para a ultima data util disponivel.
- Na borda inicial do real, se nao houver CDI anterior permitido, a data inicial pode ser resolvida para o primeiro CDI oficial dentro da tolerancia de calendario.
- A janela de CDI e `data_inicial_efetiva <= data < data_final_efetiva`.
- O CDI acumula com `fator *= 1 + taxa_diaria / 100`.
- USD/BRL usa PTAX de venda.
- Se nao houver PTAX na data resolvida, usa a cotacao anterior mais proxima.
- O fallback de USD/BRL e limitado a 15 dias.
- O calculo e o grafico consideram apenas dias uteis presentes nas series oficiais.
- A UI deve informar quando `initial_fx_date` ou `final_fx_date` diferir da data efetiva de mercado correspondente.

## Cenarios Minimos de Referencia

Os testes Python atuais ja cobrem os cenarios abaixo e a versao JavaScript deve manter equivalencia numerica nos campos essenciais.

| Cenario | Cobertura obrigatoria |
| --- | --- |
| Periodo curto em dias uteis | acumula CDI com inicio inclusivo e fim exclusivo |
| Fim de semana ou feriado | resolve inicio/fim para datas oficiais anteriores |
| Borda inicial do real | rejeita datas antes de `1994-07-01` e permite primeiro CDI oficial proximo |
| Fallback de PTAX | usa cotacao anterior dentro de 15 dias |
| Periodo invalido | rejeita data final menor/igual a inicial |
| Valor invalido | rejeita valor inicial menor/igual a zero |
| Dados insuficientes | falha com erro claro sem inventar pontos de mercado |
| Linhas invalidas | ignora datas/taxas malformadas nas series |

## Campos Comparados na Validacao Cruzada

- `final_brl`
- `cdi_percentage`
- `effective_start_date`
- `effective_end_date`
- `initial_fx_date`
- `final_fx_date`
- `real_usd_return_percentage`
- `cdi_days_used`

Differences numericas aceitaveis devem ficar dentro de tolerancia de ponto flutuante de `1e-9` para testes sinteticos e `1e-7` para comparacoes com datasets exportados.
