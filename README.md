# Armadilha do CDI

Aplicacao web estatica para comparar o crescimento nominal de um capital em CDI com a variacao do USD/BRL no mesmo periodo.

A pergunta central do projeto e:

> Se um capital ficou aplicado em CDI entre duas datas, a posicao relativa em dolar melhorou, piorou ou apenas pareceu ter melhorado em reais?

O app nao e uma calculadora generica de renda fixa. Ele mostra o capital em BRL corrigido pelo CDI, a variacao do cambio USD/BRL e a posicao equivalente em USD, mantendo essas tres leituras separadas.

Como o real brasileiro entrou em circulacao em 01/07/1994, a aplicacao aceita apenas periodos iniciados nessa data ou depois dela.

## Estado Atual

A unica superficie publicada e a versao estatica em `public/`, servida pelo Cloudflare Pages:

- calculo financeiro em JavaScript puro no navegador;
- dataset JSON versionado em `public/data/`;
- atualizacao diaria do dataset por GitHub Actions;
- grafico SVG sem dependencia de servidor;
- validacao cruzada Python/JavaScript para preservar o contrato financeiro;
- nenhuma consulta ao Banco Central durante a interacao do usuario.

Os scripts Python permanecem como infraestrutura de dados, validacao e referencia de calculo. Eles geram o dataset estatico, sincronizam cache JSON local e comparam o nucleo Python com a implementacao JavaScript.

## Saidas

A analise estatica apresenta tres blocos:

- **Capital em BRL pelo CDI**: valor inicial em BRL, valor final com CDI, CDI acumulado, equivalentes mensal/anual e dias uteis usados.
- **Cambio USD/BRL**: PTAX venda inicial e final, variacao acumulada do USD/BRL e equivalentes mensal/anual do cambio.
- **Posicao equivalente em USD**: valor inicial convertido para USD, valor final convertido para USD e variacao acumulada/equivalente da posicao em USD.

O grafico mostra:

- `CDI acumulado (%)`;
- `USD/BRL acumulado (%)`;
- `Variacao em USD`.

Por enquanto, o app nao exibe "resultado pratico" conclusivo, porque essa conclusao dependeria de uma comparacao com IPCA ou outra medida de poder de compra que ainda nao faz parte do MVP.

## Regra De Calculo

### CDI

A janela oficial do CDI e:

```python
data_inicial_efetiva <= data < data_final_efetiva
```

Quando a data inicial ou final solicitada nao possui dado oficial de mercado, o app usa a ultima data util disponivel na serie CDI. Ha uma excecao na borda inicial do real: se a data inicial solicitada estiver antes do primeiro CDI oficial disponivel, mas em ou depois de 01/07/1994, o app usa o primeiro CDI oficial disponivel dentro da tolerancia de calendario.

Para cada taxa diaria da janela:

```python
fator_acumulado *= 1 + (taxa_diaria / 100)
```

Depois:

```python
valor_final_brl = valor_inicial_brl * fator_acumulado
cdi_percentual = (fator_acumulado - 1) * 100
```

As taxas equivalentes mensal e anual usam o percentual acumulado do periodo observado e a quantidade de dias uteis de CDI efetivamente considerados:

```python
taxa_equivalente = ((1 + percentual_periodo / 100) ** (dias_equivalentes / dias_uteis) - 1) * 100
```

O ano equivalente usa `252` dias uteis e o mes equivalente usa `22` dias uteis. Essa equivalencia e uma anualizacao/mensalizacao matematica do periodo historico observado, nao uma previsao.

### USD/BRL

O app usa PTAX de venda. Quando nao existe cotacao na data solicitada, ele usa a ultima cotacao anterior disponivel, limitada a 15 dias.

```python
usd_inicial = valor_inicial_brl / cotacao_inicial
usd_final_com_cdi = valor_final_brl / cotacao_final
variacao_percentual_usd = (usd_final_com_cdi / usd_inicial - 1) * 100
```

A metrica central continua sendo `real_usd_return_percentage`, mas a interface a apresenta como posicao equivalente em USD, sem transformar esse numero em conclusao de poder de compra.

## Estrutura

```text
.
|-- .github/
|   `-- workflows/
|       |-- tests.yml
|       `-- update-static-market-data.yml
|-- package.json
|-- armadilha_cdi/
|   |-- config.py
|   |-- exceptions.py
|   |-- models.py
|   `-- services/
|       |-- cache.py
|       |-- calculations.py
|       `-- data_providers.py
|-- docs/
|   |-- archive/
|   |   `-- plano-publicacao-estatica.md
|   |-- arquitetura.md
|   |-- contrato-calculo-estatico.md
|   |-- dataset-estatico.md
|   |-- metodologia.md
|   |-- publicacao.md
|   `-- referencias.md
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
|-- tests/
|   |-- fixtures/
|   |-- js/
|   |-- test_cache.py
|   |-- test_calculations.py
|   |-- test_data_providers.py
|   `-- test_static_export.py
|-- AGENTS.md
|-- requirements.txt
`-- README.md
```

Camadas principais:

- `public/`: publicacao estatica servida pelo Cloudflare Pages.
- `public/assets/calculations.js`: calculo financeiro no navegador.
- `public/assets/presentation.js`: derivados de apresentacao para BRL, cambio e USD.
- `public/assets/app.js`: UI estatica, renderizacao da analise e grafico.
- `armadilha_cdi/services/calculations.py`: fonte de verdade Python para a regra financeira.
- `armadilha_cdi/services/data_providers.py`: integracao com Banco Central e sincronizacao do cache.
- `armadilha_cdi/services/cache.py`: cache JSON local usado pelos scripts de dados.
- `scripts/export_static_market_data.py`: exportacao do dataset estatico versionado.
- `scripts/validate_static_reference_cases.py`: validacao cruzada Python/JavaScript.
- `docs/archive/plano-publicacao-estatica.md`: plano historico da migracao para Cloudflare Pages.

## Como Rodar

Requisitos:

- Python 3.12 ou superior;
- Node.js compativel com `node --test`.

Instalacao local:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Servir a versao estatica localmente:

```bash
python3 -m http.server 8000 --directory public
```

Testes:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
```

Gerar dataset estatico e validar equivalencia Python/JavaScript:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

Sincronizar/preaquecer o cache JSON local:

```bash
python3 scripts/sync_market_data.py --start 2020-01-01
```

## Cache

O cache JSON local em `cache/` evita recapturar todo o historico do Banco Central a cada exportacao. Ele e ignorado pelo Git e serve apenas como apoio operacional para os scripts.

As escritas sao feitas por arquivo temporario seguido de substituicao atomica, com lock por arquivo durante load/merge/save.

Arquivos esperados em runtime:

- `cache/cdi.json`;
- `cache/usd.json`.

## Publicacao

A publicacao e exclusivamente estatica:

- Cloudflare Pages serve `public/`;
- GitHub Actions atualiza `public/data/market-data.latest.json` e `public/data/market-data.manifest.json`;
- o navegador calcula os resultados sem chamadas ao Banco Central durante a interacao do usuario.

Guia operacional: [docs/publicacao.md](docs/publicacao.md).

## Fontes De Dados

- CDI: serie 12 do SGS/BCB;
- USD/BRL: PTAX de venda via API Olinda do Banco Central.

Veja links e observacoes em [docs/referencias.md](docs/referencias.md).

## Limitacoes

- A disponibilidade dos dados depende dos servicos publicos do Banco Central.
- A menor data selecionavel no app e 01/07/1994, data de entrada em circulacao do real brasileiro.
- A PTAX e uma referencia oficial, nao a taxa efetiva de uma operacao individual.
- Calculos, graficos e tabelas consideram apenas dias uteis presentes nas series oficiais.
- O app ainda nao considera IPCA, impostos, taxas, spread cambial, IOF ou custos operacionais.
- Inflacao americana e poder de compra real em USD seguem como extensoes futuras.

## Roadmap Sugerido

- incluir IPCA como serie opcional;
- avaliar inflacao americana como camada adicional de leitura em USD;
- avaliar cache em storage de objetos ou outro servico gerenciado caso o JSON local do workflow deixe de ser suficiente.
