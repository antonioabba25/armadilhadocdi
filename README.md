# Armadilha do CDI

Aplicacao web em Streamlit para comparar o rendimento nominal de um capital em CDI com a variacao do USD/BRL no mesmo periodo.

A pergunta central do projeto e:

> Se eu deixei meu dinheiro rendendo CDI entre duas datas, minha posicao relativa em dolar melhorou, piorou ou apenas pareceu ter melhorado em reais?

O app nao e uma calculadora generica de renda fixa. Ele mostra se o ganho em BRL foi suficiente para preservar ou aumentar o equivalente em USD.

Como o real brasileiro entrou em circulacao em 01/07/1994, a aplicacao aceita apenas periodos iniciados nessa data ou depois dela.

## Estado atual

O MVP atual cobre:

- entrada de `data inicial`, `data final` e `valor inicial investido` em BRL;
- busca de CDI diario pela serie 12 do SGS/BCB;
- busca de USD/BRL pela PTAX de venda via API Olinda/BCB;
- cache configuravel: JSON local para desenvolvimento ou Postgres/Supabase para publicacao;
- escrita atomica e lock por arquivo no cache local, e `UPSERT` transacional no Postgres/Supabase;
- script de sincronizacao manual/agendavel para preaquecer o cache sem depender da primeira requisicao de usuario;
- calculo analitico do capital corrigido pelo CDI;
- conversao do capital inicial e final para USD;
- grafico comparativo com CDI acumulado, USD acumulado e ganho real em USD.

Os scripts exploratorios que deram origem ao produto ja foram consolidados na documentacao e removidos da base ativa. A fonte de verdade agora e o pacote `armadilha_cdi/`, seus testes e os documentos em `docs/`.

## Saidas

Resumo analitico:

- periodo analisado;
- valor inicial em BRL;
- valor final corrigido pelo CDI em BRL;
- CDI acumulado no periodo;
- cotacao USD/BRL inicial usada;
- cotacao USD/BRL final usada;
- equivalente em USD no inicio;
- equivalente em USD no fim apos CDI;
- ganho real em USD;
- datas efetivas das cotacoes quando houve fallback.
- periodo efetivo de mercado quando as datas solicitadas caem fora de dias uteis oficiais.

Grafico:

- `CDI Acumulado (%)`;
- `USD Acumulado (%)`;
- `Ganho Real em USD (%)`.

## Regra de calculo

### CDI

A janela oficial do CDI e:

```python
data_inicial_efetiva <= data < data_final_efetiva
```

Quando a data inicial ou final solicitada nao possui dado oficial de mercado, o app usa a ultima data util disponivel na serie CDI. A data final efetiva continua sendo o limite superior exclusivo.

Para cada taxa diaria da janela:

```python
fator_acumulado *= 1 + (taxa_diaria / 100)
```

Depois:

```python
valor_final_brl = valor_inicial_brl * fator_acumulado
cdi_percentual = (fator_acumulado - 1) * 100
```

### USD/BRL

O app usa PTAX de venda. Quando nao existe cotacao na data solicitada, ele usa a ultima cotacao anterior disponivel, limitada a 15 dias.

```python
usd_inicial = valor_inicial_brl / cotacao_inicial
usd_final_com_cdi = valor_final_brl / cotacao_final
rentabilidade_usd_real = (usd_final_com_cdi / usd_inicial - 1) * 100
```

Interpretacao:

- positivo: ganhou poder relativo em USD;
- perto de zero: preservou aproximadamente a posicao;
- negativo: perdeu poder relativo em USD, mesmo que tenha subido em BRL.

## Estrutura

```text
.
|-- app.py
|-- armadilha_cdi/
|   |-- config.py
|   |-- exceptions.py
|   |-- models.py
|   `-- services/
|       |-- cache.py
|       |-- calculations.py
|       |-- charts.py
|       `-- data_providers.py
|-- docs/
|   |-- arquitetura.md
|   |-- metodologia.md
|   `-- referencias.md
|-- scripts/
|   `-- sync_market_data.py
|-- tests/
|   |-- test_cache.py
|   |-- test_calculations.py
|   |-- test_charts.py
|   `-- test_data_providers.py
|-- AGENTS.md
|-- requirements.txt
`-- README.md
```

Camadas principais:

- `app.py`: interface Streamlit, formulario, resumo, grafico e mensagens de erro;
- `data_providers.py`: integracao com Banco Central e sincronizacao do cache;
- `cache.py`: contrato de cache, backend JSON local e backend Postgres/Supabase;
- `calculations.py`: validacao, acumulacao de CDI e resolucao de cotacoes;
- `charts.py`: preparacao das series comparativas do grafico;
- `models.py`: dataclasses compartilhadas entre camadas;
- `scripts/sync_market_data.py`: sincronizacao manual ou agendada do cache;
- `tests/`: garantia das regras financeiras centrais.

## Como rodar

Requisitos:

- Python 3.12 ou superior.

Instalacao e execucao:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Testes:

```bash
python3 -m unittest discover -s tests -v
```

Sincronizar/preaquecer o cache local:

```bash
python3 scripts/sync_market_data.py --start 2020-01-01
```

Sincronizar/preaquecer o cache no Supabase:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
python3 scripts/sync_market_data.py --start 2020-01-01
```

## Cache e Supabase

O cache funciona como camada de sincronizacao com o Banco Central: o app consulta primeiro os dados persistidos, completa as janelas ausentes na fonte oficial e grava o merge para consultas futuras.

As consultas de CDI ao SGS/BCB sao fatiadas internamente em janelas menores, com uma pequena pausa entre requisicoes. Isso contorna limites de janela em series diarias e reduz falhas em periodos longos sem alterar a regra de calculo.

Por padrao, o backend e JSON local em `cache/`, ignorado pelo Git. Ele e adequado para desenvolvimento e execucao local. Pode ser apagado quando necessario; o app recria os arquivos ao consultar o Banco Central novamente.

No backend local, as escritas sao feitas por arquivo temporario seguido de substituicao atomica, com lock por arquivo durante load/merge/save. Isso torna o cache local mais seguro para o modelo do Streamlit, mas ele continua sendo uma opcao de desenvolvimento. Para publicacao, use o backend Supabase/Postgres.

Arquivos esperados em runtime:

- `cache/cdi.json`;
- `cache/usd.json`.

Arquivos `*.lock` ou temporarios dentro de `cache/` podem aparecer durante execucao e nao devem ser versionados.

Para publicacao, use o backend Supabase/Postgres:

```toml
# .streamlit/secrets.toml ou secrets da plataforma
MARKET_DATA_CACHE_BACKEND = "supabase"
SUPABASE_DATABASE_URL = "postgresql://..."
# opcional
SUPABASE_CACHE_TABLE = "market_rates"
```

O app cria automaticamente a tabela se ela ainda nao existir:

```sql
create table if not exists market_rates (
  series text not null,
  ref_date date not null,
  value numeric not null,
  updated_at timestamptz not null default now(),
  primary key (series, ref_date)
);
```

Use a connection string Postgres do Supabase no servidor. Para ambientes sem IPv6 ou com muitas conexoes temporarias, prefira a string do pooler indicada pelo Supabase. O valor de `SUPABASE_DATABASE_URL` e segredo e nao deve ser versionado.

## Fontes de dados

- CDI: serie 12 do SGS/BCB;
- USD/BRL: PTAX de venda via API Olinda do Banco Central.

Veja links e observacoes em [docs/referencias.md](docs/referencias.md).

## Limitacoes

- A disponibilidade depende dos servicos publicos do Banco Central.
- A menor data selecionavel no app e 01/07/1994, data de entrada em circulacao do real brasileiro.
- A PTAX e uma referencia oficial, nao a taxa efetiva de uma operacao individual.
- Calculos, graficos e tabelas consideram apenas dias uteis presentes nas series oficiais.
- O grafico atual nao inclui IPCA.
- Inflacao americana e poder de compra real em USD seguem como extensoes futuras, fora do MVP atual.

## Roadmap sugerido

- adicionar endpoint HTTP para consumo externo;
- incluir IPCA como serie opcional;
- avaliar inflacao americana como camada adicional de leitura em USD;
- adicionar rotina agendada de sincronizacao diaria do cache Supabase;
- avaliar cache de leitura em memoria no Streamlit sobre o backend persistente.
