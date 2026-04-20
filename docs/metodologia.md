# Metodologia de Calculo

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

## Regra temporal consolidada

Depois de comparar os blocos do notebook exploratorio, a regra escolhida para o app foi:

`data_inicial <= data < data_final`

Na pratica, isso significa:

- a taxa de CDI da data inicial entra no acumulo;
- a data final funciona como limite superior exclusivo;
- essa convencao evita ambiguidades e reproduz a regra marcada como validada no material exploratorio.

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

## Etapa 2: resolucao das cotacoes USD/BRL

Nem toda data possui cotacao PTAX disponivel. Isso acontece, por exemplo, em fins de semana e feriados.

Por isso, o app aplica uma regra explicita de fallback:

- tenta encontrar a cotacao exata na data solicitada;
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

## Etapa 4: ganho real em USD

Essa e a metrica central do produto:

```python
rentabilidade_usd_real = (usd_final_com_cdi / usd_inicial - 1) * 100
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
rentabilidade_usd_real = (2692.31 / 2500.00 - 1) * 100 = 7.69%
```

Embora o capital tenha crescido em reais, o que interessa aqui e que ele terminou com mais dolares equivalentes do que no inicio.

## Series do grafico

O grafico do MVP enfatiza comparacao e nao apenas resultado final. As series atuais sao:

- `CDI Acumulado (%)`
- `USD Acumulado (%)`
- `Ganho Real em USD (%)`

Leitura sugerida:

- se a curva do USD sobe mais rapido do que a curva do CDI, o real tende a perder terreno;
- se a curva de ganho real em USD fica negativa, o investidor teve erosao de poder relativo em dolar;
- se a curva de ganho real em USD sobe, o CDI compensou a variacao cambial e ainda gerou ganho relativo.

## O que esta fora do MVP

O notebook exploratorio tambem cita IPCA e existe um arquivo complementar sobre inflacao americana. Isso ajuda a enquadrar o problema de forma mais ampla, mas nao faz parte do contrato minimo atual da aplicacao.

Nesta versao, o nucleo obrigatorio continua sendo:

- CDI
- USD/BRL
- comparacao de poder relativo em dolar
