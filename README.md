# Armadilha do CDI

Aplicacao web em Streamlit para responder uma pergunta que muita analise de renda fixa ignora:

> deixar o dinheiro rendendo CDI em reais foi suficiente para preservar ou aumentar o seu poder relativo em dolar?

O projeto compara o crescimento nominal de um capital em BRL com a variacao do USD/BRL no mesmo periodo. O objetivo nao e mostrar apenas "quanto rendeu", mas revelar se o ganho aparente em reais realmente resistiu quando observado em moeda forte.

## Problema que o app resolve

Uma analise tradicional pode dizer:

- "o investimento rendeu X% em CDI";
- "o valor final em reais ficou maior";
- "logo, houve ganho."

Este projeto parte de uma leitura mais economica:

- se o real se desvalorizou muito no periodo;
- e se o capital corrigido pelo CDI compra menos dolares no fim;
- entao o investidor pode ter tido ganho nominal em BRL, mas perda relativa em USD.

Essa e a "armadilha do CDI" que o app tenta explicitar.

## O que a aplicacao entrega

Entradas:

- data inicial
- data final
- valor inicial investido em BRL

Saidas analiticas:

- periodo analisado
- valor inicial em BRL
- valor final corrigido pelo CDI em BRL
- CDI acumulado no periodo
- cotacao USD/BRL inicial usada
- cotacao USD/BRL final usada
- equivalente em USD no inicio
- equivalente em USD no fim apos correcao pelo CDI
- ganho real em USD

Saida grafica:

- CDI acumulado (%)
- USD acumulado (%)
- ganho real em USD (%)

## Como o calculo funciona

### 1. Acumulo do CDI

O nucleo do calculo segue a regra consolidada a partir do notebook exploratorio:

`data_inicial <= data < data_final`

Para cada dia util de CDI dentro dessa janela:

```python
fator_acumulado *= (1 + taxa_diaria / 100)
```

Depois:

```python
valor_final_brl = valor_inicial_brl * fator_acumulado
cdi_percentual = (fator_acumulado - 1) * 100
```

### 2. Conversao para dolar

O app busca a cotacao USD/BRL de venda no inicio e no fim do periodo. Se nao existir cotacao exata na data pedida, ele procura a cotacao anterior mais proxima, com limite de 15 dias.

```python
usd_inicial = valor_inicial_brl / cotacao_inicial
usd_final_com_cdi = valor_final_brl / cotacao_final
rentabilidade_usd_real = (usd_final_com_cdi / usd_inicial - 1) * 100
```

### 3. Interpretacao

- resultado positivo em USD: houve ganho relativo em dolar
- resultado proximo de zero: o capital apenas preservou aproximadamente a posicao relativa
- resultado negativo em USD: houve perda relativa em dolar, mesmo com ganho nominal em reais

## Regras de negocio adotadas

- Janela do CDI: `data_inicial <= data < data_final`
- Fallback de USD/BRL: usa a ultima cotacao anterior disponivel, com limite de 15 dias
- Metrica principal: `rentabilidade_usd_real`
- Cache local: arquivos JSON para evitar buscar todo o historico a cada consulta
- Transparencia: a interface informa quando houve uso de fallback de cotacao

## Arquitetura do projeto

```text
armadilha_cdi/
  services/
    cache.py
    calculations.py
    charts.py
    data_providers.py
  config.py
  exceptions.py
  models.py
app.py
docs/
tests/
exploracaonotebook/
```

Camadas principais:

- `app.py`: interface Streamlit, formulario e exibicao dos resultados
- `armadilha_cdi/services/data_providers.py`: integracao com Banco Central
- `armadilha_cdi/services/cache.py`: persistencia local do cache
- `armadilha_cdi/services/calculations.py`: regra de negocio principal
- `armadilha_cdi/services/charts.py`: preparacao das series exibidas no grafico
- `tests/`: testes unitarios da regra financeira e do dataset grafico

## Inspiracao conceitual

Este projeto nasceu a partir de dois arquivos exploratorios:

- `exploracaonotebook/calc_armadilhacdi.py`
- `calculo_inflacaoamericana.py`

O primeiro define o fluxo central do MVP: `CDI + USD/BRL`. O segundo ajuda a reforcar a leitura do problema como preservacao de poder de compra em moeda forte, servindo como referencia para possiveis expansoes futuras.

## Requisitos

- Python 3.12+

## Como rodar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Como executar os testes

```bash
python3 -m unittest discover -s tests -v
```

## Documentacao complementar

- [Arquitetura](docs/arquitetura.md)
- [Metodologia de calculo](docs/metodologia.md)
- [Referencias](docs/referencias.md)

## Fontes de dados

- CDI: serie 12 do SGS/BCB
- USD/BRL: PTAX via API Olinda do Banco Central

## Limitacoes atuais

- o app depende da disponibilidade dos servicos publicos do Banco Central;
- o grafico do MVP ainda nao inclui IPCA;
- a analise em dolar usa PTAX como referencia, nao a cotacao efetivamente negociada por um investidor;
- a camada inspirada em inflacao americana ainda nao faz parte do fluxo minimo da aplicacao.

## Roadmap sugerido

- adicionar endpoint HTTP para consumo por frontend ou terceiros;
- incluir IPCA como serie opcional no grafico;
- considerar uma camada futura de comparacao com inflacao americana;
- evoluir o cache para uma estrategia mais robusta em producao.
