# Referencias

## Referencias oficiais de dados

### Banco Central do Brasil

- SGS - API de series temporais: https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados
- PTAX - documentacao da API Olinda: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
- PTAX - conjunto de dados no portal de dados abertos: https://dadosabertos.bcb.gov.br/dataset/dolar-americano-usd-todos-os-boletins-diarios
- FAQ do BCB sobre taxas divulgadas e PTAX: https://www.bcb.gov.br/meubc/faqs/p/o-que-significam-as-taxas-divulgadas-pelo-banco-central

## Referencias de publicacao

- Streamlit Community Cloud: https://streamlit.io/cloud
- Deploy no Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Secrets no Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Billing e quotas do Supabase: https://supabase.com/docs/guides/platform/billing-on-supabase

## Referencias complementares para extensoes futuras

### FRED / Federal Reserve Bank of St. Louis

- CPIAUCSL - Consumer Price Index for All Urban Consumers: All Items in U.S. City Average: https://fred.stlouisfed.org/series/CPIAUCSL

Essa serie nao entra no MVP atual do app, mas pode apoiar uma extensao futura de analise de poder de compra em USD.

### IPCA / Banco Central

- IPCA - serie 433 do SGS/BCB: https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados

Essa serie tambem esta fora do MVP atual, mas e uma candidata natural para enriquecer o grafico comparativo.

## Observacoes metodologicas

- O app usa a serie `12` do SGS para CDI, conforme implementado em `armadilha_cdi/services/data_providers.py`.
- O app usa a cotacao de venda (`cotacaoVenda`) da PTAX para USD/BRL.
- A PTAX e uma taxa de referencia publica e nao necessariamente a taxa efetiva de uma operacao individual de cambio.
- As referencias exploratorias antigas foram removidas da base ativa; a memoria tecnica do projeto esta consolidada em `README.md`, `AGENTS.md` e `docs/`.
