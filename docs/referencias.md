# Referencias

## Referencias oficiais de dados

### Banco Central do Brasil

- SGS - API de series temporais: https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados
- PTAX - documentacao da API Olinda: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
- PTAX - conjunto de dados no portal de dados abertos: https://dadosabertos.bcb.gov.br/dataset/dolar-americano-usd-todos-os-boletins-diarios
- FAQ do BCB sobre taxas divulgadas e PTAX: https://www.bcb.gov.br/meubc/faqs/p/o-que-significam-as-taxas-divulgadas-pelo-banco-central

## Referencia complementar

### FRED / Federal Reserve Bank of St. Louis

- CPIAUCSL - Consumer Price Index for All Urban Consumers: All Items in U.S. City Average: https://fred.stlouisfed.org/series/CPIAUCSL

Essa serie nao entra no MVP atual do app, mas aparece como referencia conceitual para extensoes futuras de analise de poder de compra em USD.

## Referencias internas do repositorio

- `exploracaonotebook/calc_armadilhacdi.py`: arquivo exploratorio principal que consolidou a intuicao do produto e a regra financeira atual.
- `calculo_inflacaoamericana.py`: referencia complementar para a leitura do problema como preservacao de poder de compra em moeda forte.

## Observacoes metodologicas

- O app usa a serie `12` do SGS para CDI, conforme implementado em `armadilha_cdi/services/data_providers.py`.
- O app usa a cotacao de venda (`cotacaoVenda`) da PTAX para USD/BRL.
- A PTAX e uma taxa de referencia publica e nao necessariamente a taxa efetiva de uma operacao individual de cambio.
