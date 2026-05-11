# Armadilha do CDI

Aplicação web para comparar o crescimento nominal de um capital em CDI com a variação do USD/BRL no mesmo período.

A pergunta central do projeto é:

> Se um capital ficou aplicado em CDI entre duas datas, a posição relativa em dólar melhorou, piorou ou apenas pareceu ter melhorado em reais?

O app não é uma calculadora genérica de renda fixa. Ele mostra o capital em BRL corrigido pelo CDI, a variação do câmbio USD/BRL e a posição equivalente em USD, mantendo essas três leituras separadas.

Como o real brasileiro entrou em circulação em 01/07/1994, a aplicação aceita apenas períodos iniciados nessa data ou depois dela.

## Estado Atual

A superfície pública principal é a versão estática em `public/`, publicada em Cloudflare Pages:

- cálculo financeiro em JavaScript puro no navegador;
- dataset JSON versionado em `public/data/`;
- atualização diária do dataset por GitHub Actions;
- gráfico SVG sem dependência de servidor;
- validação cruzada Python/JavaScript para preservar o contrato financeiro.

O Streamlit continua na base como referência funcional, ferramenta local/admin e implementação Python pura. Ele usa o mesmo núcleo de cálculo, pode consultar o Banco Central sob demanda e suporta cache JSON local ou Postgres/Supabase.

Os scripts exploratórios antigos foram removidos da base ativa. As decisões úteis foram consolidadas em `README.md`, `AGENTS.md`, `docs/metodologia.md`, `docs/arquitetura.md` e nos materiais históricos em `docs/archive/`.

## Saídas

A análise estática apresenta três blocos:

- **Capital em BRL pelo CDI**: valor inicial em BRL, valor final com CDI, CDI acumulado, equivalentes mensal/anual e dias úteis usados.
- **Câmbio USD/BRL**: PTAX venda inicial e final, variação acumulada do USD/BRL e equivalentes mensal/anual do câmbio.
- **Posição equivalente em USD**: valor inicial convertido para USD, valor final convertido para USD e variação acumulada/equivalente da posição em USD.

O gráfico mostra:

- `CDI acumulado (%)`;
- `USD/BRL acumulado (%)`;
- `Variação em USD`.

Por enquanto, o app não exibe “resultado prático” conclusivo, porque essa conclusão dependeria de uma comparação com IPCA ou outra medida de poder de compra que ainda não faz parte do MVP.

## Regra De Cálculo

### CDI

A janela oficial do CDI é:

```python
data_inicial_efetiva <= data < data_final_efetiva
```

Quando a data inicial ou final solicitada não possui dado oficial de mercado, o app usa a última data útil disponível na série CDI. Há uma exceção na borda inicial do real: se a data inicial solicitada estiver antes do primeiro CDI oficial disponível, mas em ou depois de 01/07/1994, o app usa o primeiro CDI oficial disponível dentro da tolerância de calendário.

Para cada taxa diária da janela:

```python
fator_acumulado *= 1 + (taxa_diaria / 100)
```

Depois:

```python
valor_final_brl = valor_inicial_brl * fator_acumulado
cdi_percentual = (fator_acumulado - 1) * 100
```

As taxas equivalentes mensal e anual usam o percentual acumulado do período observado e a quantidade de dias úteis de CDI efetivamente considerados:

```python
taxa_equivalente = ((1 + percentual_periodo / 100) ** (dias_equivalentes / dias_uteis) - 1) * 100
```

O ano equivalente usa `252` dias úteis e o mês equivalente usa `22` dias úteis. Essa equivalência é uma anualização/mensalização matemática do período histórico observado, não uma previsão.

### USD/BRL

O app usa PTAX de venda. Quando não existe cotação na data solicitada, ele usa a última cotação anterior disponível, limitada a 15 dias.

```python
usd_inicial = valor_inicial_brl / cotacao_inicial
usd_final_com_cdi = valor_final_brl / cotacao_final
variacao_percentual_usd = (usd_final_com_cdi / usd_inicial - 1) * 100
```

A métrica central continua sendo `real_usd_return_percentage`, mas a interface a apresenta como posição equivalente em USD, sem transformar esse número em conclusão de poder de compra.

## Estrutura

```text
.
|-- .github/
|   `-- workflows/
|       `-- update-static-market-data.yml
|-- app.py
|-- package.json
|-- armadilha_cdi/
|   |-- config.py
|   |-- exceptions.py
|   |-- frontpage_texts.py
|   |-- models.py
|   `-- services/
|       |-- cache.py
|       |-- calculations.py
|       |-- charts.py
|       `-- data_providers.py
|-- docs/
|   |-- archive/
|   |   |-- frontpage_formatacao.md
|   |   `-- plano-publicacao-estatica.md
|   |-- arquitetura.md
|   |-- contrato-calculo-estatico.md
|   |-- dataset-estatico.md
|   |-- metodologia.md
|   |-- publicacao.md
|   |-- referencias.md
|   `-- streamlit-secrets.example.toml
|-- public/
|   |-- index.html
|   |-- assets/
|   |   |-- app.js
|   |   |-- calculations.js
|   |   |-- presentation.js
|   |   `-- styles.css
|   `-- data/
|       |-- market-data.latest.json
|       `-- market-data.manifest.json
|-- scripts/
|   |-- export_static_market_data.py
|   |-- js_calculate_static.mjs
|   |-- sync_market_data.py
|   `-- validate_static_reference_cases.py
|-- supabase/
|   `-- migrations/
|       `-- 20260501000000_create_market_rates.sql
|-- tests/
|   |-- fixtures/
|   |-- js/
|   |-- test_cache.py
|   |-- test_calculations.py
|   |-- test_charts.py
|   |-- test_data_providers.py
|   `-- test_static_export.py
|-- AGENTS.md
|-- requirements.txt
`-- README.md
```

Camadas principais:

- `public/`: publicação estática servida pelo Cloudflare Pages.
- `public/assets/calculations.js`: cálculo financeiro no navegador.
- `public/assets/presentation.js`: derivados de apresentação para BRL, câmbio e USD.
- `public/assets/app.js`: UI estática, renderização da análise e gráfico.
- `armadilha_cdi/services/calculations.py`: fonte de verdade Python para a regra financeira.
- `armadilha_cdi/services/data_providers.py`: integração com Banco Central e sincronização do cache.
- `armadilha_cdi/services/cache.py`: contrato de cache, JSON local e Postgres/Supabase.
- `scripts/export_static_market_data.py`: exportação do dataset estático versionado.
- `scripts/validate_static_reference_cases.py`: validação cruzada Python/JavaScript.
- `docs/archive/plano-publicacao-estatica.md`: plano histórico da migração para Cloudflare Pages.

## Como Rodar

Requisitos:

- Python 3.12 ou superior;
- Node.js compatível com `node --test`.

Instalação local do Streamlit:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Servir a versão estática localmente:

```bash
python3 -m http.server 8000 --directory public
```

Testes:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
```

Gerar dataset estático e validar equivalência Python/JavaScript:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
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

## Cache E Supabase

O cache funciona como camada de sincronização com o Banco Central: o app consulta primeiro os dados persistidos, completa as janelas ausentes na fonte oficial e grava o merge para consultas futuras.

Por padrão, o backend é JSON local em `cache/`, ignorado pelo Git. Ele é adequado para desenvolvimento e execução local.

No backend local, as escritas são feitas por arquivo temporário seguido de substituição atômica, com lock por arquivo durante load/merge/save. Para publicação Streamlit, prefira o backend Supabase/Postgres.

Arquivos esperados em runtime:

- `cache/cdi.json`;
- `cache/usd.json`.

Para publicação Streamlit com Supabase/Postgres:

```toml
MARKET_DATA_CACHE_BACKEND = "supabase"
SUPABASE_DATABASE_URL = "postgresql://..."
SUPABASE_CACHE_TABLE = "market_rates"
```

O app cria automaticamente a tabela se ela ainda não existir. Para setup manual ou auditoria do schema, use `supabase/migrations/20260501000000_create_market_rates.sql`.

## Publicação

A publicação principal é estática:

- Cloudflare Pages serve `public/`;
- GitHub Actions atualiza `public/data/market-data.latest.json` e `public/data/market-data.manifest.json`;
- o navegador calcula os resultados sem chamadas ao Banco Central durante a interação do usuário.

O Streamlit permanece como caminho alternativo/admin:

- Streamlit Community Cloud para hospedar `app.py`;
- Supabase Free como cache Postgres persistente;
- secrets configurados no painel do Streamlit, nunca no repositório;
- cache pre-aquecido com `scripts/sync_market_data.py` antes de uso público.

Guia operacional: [docs/publicacao.md](docs/publicacao.md).

## Fontes De Dados

- CDI: série 12 do SGS/BCB;
- USD/BRL: PTAX de venda via API Olinda do Banco Central.

Veja links e observações em [docs/referencias.md](docs/referencias.md).

## Limitações

- A disponibilidade dos dados depende dos serviços públicos do Banco Central.
- A menor data selecionável no app é 01/07/1994, data de entrada em circulação do real brasileiro.
- A PTAX é uma referência oficial, não a taxa efetiva de uma operação individual.
- Cálculos, gráficos e tabelas consideram apenas dias úteis presentes nas séries oficiais.
- O app ainda não considera IPCA, impostos, taxas, spread cambial, IOF ou custos operacionais.
- Inflação americana e poder de compra real em USD seguem como extensões futuras.

## Roadmap Sugerido

- incluir IPCA como série opcional;
- avaliar inflação americana como camada adicional de leitura em USD;
- manter o Streamlit como ferramenta local/admin enquanto fizer sentido;
- avaliar cache de leitura em memória no Streamlit sobre o backend persistente.
