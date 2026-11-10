# Metodologia e Contrato de Calculo

Documento principal das regras financeiras e do contrato Python/JavaScript. Consulte [arquitetura](arquitetura.md) para responsabilidades e [referencias](referencias.md) para fontes oficiais.

## Visao geral

O projeto foi desenhado para responder a uma pergunta simples, mas economicamente mais exigente do que uma calculadora tradicional de renda fixa:

> um capital aplicado em CDI entre duas datas terminou o periodo com mais ou menos poder relativo em dolar?

Para responder isso, o app combina duas series:

- CDI diario
- USD/BRL de venda via PTAX

## Entradas

O calculo parte de tres entradas obrigatorias:

- `data inicial`
- `data final`
- `valor inicial investido` em BRL

Como o real brasileiro entrou em circulacao em 01/07/1994, a `data inicial` deve ser 01/07/1994 ou posterior. Dados de CDI ou USD/BRL anteriores a essa data nao sao usados como fallback do periodo inicial.

## Regra temporal consolidada

A regra temporal consolidada para o app e:

`data_inicial_efetiva <= data < data_final_efetiva`

Na pratica, isso significa:

- se a data solicitada nao tiver dado oficial, o app usa a ultima data util disponivel na serie CDI, dentro de 15 dias (`MAX_MARKET_DATE_FALLBACK_DAYS`);
- na borda inicial do real, se nao houver CDI anterior permitido e a primeira observacao oficial estiver dentro da tolerancia de calendario, o app usa essa primeira data oficial;
- a taxa de CDI da data inicial efetiva entra no acumulo;
- a data final efetiva funciona como limite superior exclusivo;
- fins de semana e feriados nao entram como linhas proprias em calculos ou graficos;
- essa convencao evita ambiguidades e deve ser tratada como decisao de produto.

Na serie 12 do BCB, o primeiro CDI oficial retornado a partir da circulacao do real e `04/07/1994`. Assim, uma consulta iniciada em `01/07/1994` e analisada com periodo efetivo a partir de `04/07/1994`, sem usar dados anteriores ao real e sem criar taxa sintetica para os dias sem observacao oficial.

## Etapa 1: acumulacao do CDI

O CDI e capitalizado dia a dia dentro da janela valida:

```python
fator_acumulado = 1.0
for taxa_diaria in serie_cdi_filtrada:
    fator_acumulado *= (1 + taxa_diaria / 100)
```

Depois disso:

```python
valor_final_brl = valor_inicial_brl * fator_acumulado
cdi_percentual = (fator_acumulado - 1) * 100
```

Para contextualizar os percentuais de periodo exibidos na pagina estatica, o app calcula taxas equivalentes anual e mensal:

```python
taxa_equivalente = ((1 + percentual_periodo / 100) ** (dias_equivalentes / dias_uteis) - 1) * 100
```

O denominador `dias_uteis` e a quantidade de dias de CDI usados no periodo efetivo. O ano equivalente usa `252` dias uteis e o mes equivalente usa `22` dias uteis. Essa taxa equivalente e apenas uma anualizacao/mensalizacao matematica do percentual historico observado, nao uma previsao de retorno ou cambio.

## Etapa 2: resolucao das cotacoes USD/BRL

Nem toda data possui cotacao PTAX disponivel. Isso acontece, por exemplo, em fins de semana e feriados.

Por isso, o app aplica uma regra explicita de fallback:

- tenta encontrar a cotacao exata na data efetiva de mercado;
- se nao encontrar, retrocede dia a dia;
- limita a retroacao a 15 dias;
- informa ao usuario quando a data efetivamente usada foi diferente da data pedida.

Essa decisao evita duas falhas comuns:

- quebrar o calculo em datas sem cotacao;
- usar uma cotacao antiga demais de forma silenciosa.

## Etapa 3: conversao do capital para dolar

Com o capital inicial e final em BRL e as cotacoes inicial e final resolvidas, o app calcula:

```python
usd_inicial = valor_inicial_brl / cotacao_inicial
usd_final_com_cdi = valor_final_brl / cotacao_final
```

## Etapa 4: variacao percentual em USD

Essa e a metrica central do produto:

```python
variacao_percentual_usd = (usd_final_com_cdi / usd_inicial - 1) * 100
```

Interpretacao:

- se o resultado for positivo, o capital ganhou poder relativo em dolar;
- se for zero ou proximo de zero, apenas preservou aproximadamente a posicao;
- se for negativo, perdeu poder relativo em dolar, mesmo com ganho nominal em BRL.

## Exemplo conceitual

Suponha:

- valor inicial: `R$ 10.000`
- cotacao inicial: `4,00`
- cotacao final: `5,20`
- valor final com CDI: `R$ 14.000`

Entao:

```python
usd_inicial = 10000 / 4.00 = 2500.00
usd_final_com_cdi = 14000 / 5.20 = 2692.31
variacao_percentual_usd = (2692.31 / 2500.00 - 1) * 100 = 7.69%
```

Embora o capital tenha crescido em reais, o que interessa aqui e que ele terminou com mais dolares equivalentes do que no inicio.

## Series do grafico

O grafico do MVP enfatiza comparacao e nao apenas resultado final. As series atuais sao:

- `CDI Acumulado (%)`
- `USD/BRL Acumulado (%)`
- `Variacao % em USD`

Leitura sugerida:

- se a curva do USD sobe mais rapido do que a curva do CDI, o real tende a perder terreno;
- se a curva de variacao % em USD fica negativa, o investidor teve erosao de poder relativo em dolar;
- se a curva de variacao % em USD sobe, o CDI compensou a variacao cambial e aumentou a posicao relativa em dolar.

As linhas do grafico sao geradas apenas para dias uteis presentes na serie CDI oficial. Quando o periodo solicitado comeca ou termina em fim de semana ou feriado, a visualizacao usa o periodo efetivo de mercado.

## O que esta fora do MVP

O historico exploratorio tambem citava IPCA e inflacao americana. Isso ajuda a enquadrar o problema de forma mais ampla, mas nao faz parte do contrato minimo atual da aplicacao.

Nesta versao, o nucleo obrigatorio continua sendo:

- CDI
- USD/BRL
- comparacao de poder relativo em dolar

A UI separa capital em BRL, cambio e posicao em USD, sem apresentar conclusao de poder de compra real. O nome tecnico `real_usd_return_percentage` e preservado por compatibilidade; nao desconta inflacao americana.


## Contrato de calculo

Contrato vigente, consolidado do antigo documento de migracao em 09/11/2026. A referencia implementada e [calculate_result](../armadilha_cdi/services/calculations.py), com retorno [CalculationResult](../armadilha_cdi/models.py). O equivalente JavaScript e `calculateResult` em [calculations.js](../public/assets/calculations.js).

```python
calculate_result(
    start_date: date,
    end_date: date,
    initial_brl: float,
    cdi_rates: dict[str, float],
    usd_rates: dict[str, float],
) -> CalculationResult
```

Entradas: periodo com `end_date > start_date`, inicio em ou depois de `1994-07-01`, capital maior que zero e mapas de CDI diario percentual/PTAX venda por data ISO `YYYY-MM-DD`. Datas Python usam `date`; o JavaScript recebe strings ISO e argumentos `startDate`, `endDate`, `initialBrl`, `cdiRates`, `usdRates`.

Campos de retorno compartilhados:

| Grupo | Campos |
| --- | --- |
| Periodo | `start_date`, `end_date`, `effective_start_date`, `effective_end_date` |
| Capital/CDI | `initial_brl`, `final_brl`, `cdi_factor`, `cdi_percentage`, `cdi_days_used` |
| Cambio | `initial_usdbrl`, `final_usdbrl`, `initial_fx_date`, `final_fx_date` |
| Posicao em USD | `initial_usd`, `final_usd_with_cdi`, `real_usd_return_percentage` |

A UI informa o periodo efetivo quando difere do solicitado e destaca a PTAX quando sua data difere da data efetiva de mercado. O grafico utiliza o mesmo ajuste de datas do resultado.

## Cenarios de validacao

| Cenario | Comportamento obrigatorio |
| --- | --- |
| Periodo curto em dias uteis | Inicio inclusivo e fim exclusivo no CDI |
| Fim de semana/feriado | Usa pontos oficiais anteriores dentro da tolerancia |
| Inicio do real | Rejeita datas anteriores; aceita primeiro CDI proximo dentro da tolerancia |
| PTAX ausente | Usa cotacao anterior em ate 15 dias; falha fora da tolerancia |
| Periodo/valor invalido | Erro claro para fim menor/igual ao inicio e capital menor/igual a zero |
| Dados insuficientes | Erro claro, sem inventar pontos |
| Linhas malformadas | Ignora datas/taxas invalidas nas series |
| Grafico | Apenas datas oficiais de CDI, com fallback equivalente ao resultado |

O [comparador](../scripts/validate_static_reference_cases.py) verifica `final_brl`, `cdi_percentage`, datas efetivas de mercado/PTAX, `real_usd_return_percentage` e `cdi_days_used`. Tolerancias documentadas: `1e-9` para testes sinteticos e `1e-7` para comparacao com datasets exportados. Os caminhos dos testes estao na [arquitetura](arquitetura.md#responsabilidades-e-verificacao).
