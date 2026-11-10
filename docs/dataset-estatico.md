# Dataset Estatico de Mercado

O dataset estatico transporta dados oficiais pre-gerados para o navegador. Ele nao contem segredos e nao deve depender de consulta ao Banco Central durante a interacao do usuario.

O [exportador](../scripts/export_static_market_data.py) produz o dataset e o manifesto; a [UI](../public/assets/app.js) carrega diretamente o dataset. Operacao e diagnostico: [publicacao](publicacao.md).

## Decisao de Granularidade

A versao inicial usa arquivo unico. O historico diario de CDI e PTAX desde 1994 cabe em um JSON simples e evita complexidade prematura no carregamento. A decisao deve ser reavaliada se o arquivo comprimido deixar de ser confortavel para primeiro carregamento em rede comum.

## `public/data/market-data.latest.json`

Schema versionado. O JSON abaixo e um recorte ilustrativo, nao um dataset completo nem o estado atual da publicacao:

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-11T00:00:00Z",
  "source": {
    "cdi": "BCB SGS serie 12",
    "usdbrl": "BCB Olinda PTAX venda"
  },
  "coverage": {
    "requested_start_date": "1994-07-01",
    "requested_end_date": "2026-05-11",
    "start_date": "1994-07-01",
    "end_date": "2026-05-08",
    "cdi_start_date": "1994-07-04",
    "cdi_end_date": "2026-05-08",
    "usd_start_date": "1994-07-01",
    "usd_end_date": "2026-05-08"
  },
  "limits": {
    "earliest_supported_date": "1994-07-01",
    "max_usd_fallback_days": 15,
    "max_market_date_fallback_days": 15
  },
  "cdi_rates": {
    "2026-05-08": 0.042239
  },
  "usd_rates": {
    "2026-05-08": 5.6789
  }
}
```

Campos:

- `schema_version`: inteiro, atualmente `1`.
- `generated_at`: instante UTC de geracao em ISO 8601.
- `source`: descricao humana das fontes oficiais.
- `coverage.requested_*`: janela solicitada ao exportador.
- `coverage.start_date` e `coverage.end_date`: janela comum de publicacao usada pela interface.
- `coverage.cdi_*` e `coverage.usd_*`: limites reais de cada serie no arquivo.
- `limits`: constantes de dominio usadas pelo navegador.
- `cdi_rates`: mapa de taxa diaria percentual por data oficial.
- `usd_rates`: mapa de PTAX venda por data oficial.

## `public/data/market-data.manifest.json`

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-11T00:00:00Z",
  "latest": "market-data.latest.json",
  "coverage": {
    "start_date": "1994-07-01",
    "end_date": "2026-05-08"
  },
  "counts": {
    "cdi_rates": 7900,
    "usd_rates": 7900
  }
}
```

O manifesto permite a operadores conferir rapidamente cobertura e contagens. A UI atual nao o consulta. Os valores de exemplo nao representam a cobertura atual.

## Validacoes Obrigatorias

- Todas as datas devem estar em `YYYY-MM-DD`.
- `generated_at` deve terminar com `Z`.
- Taxas e cotacoes devem ser numeros finitos.
- `cdi_rates` e `usd_rates` nao podem estar vazios.
- A cobertura deve respeitar `1994-07-01` como minimo.
- `coverage.end_date` nao pode ultrapassar os limites reais das series.
- O arquivo publicado nao pode conter URLs de credenciais, tokens ou strings de conexao.


## Frescor e cobertura

`generated_at` e o instante de exportacao, nao a data da ultima observacao do BCB. `coverage.requested_end_date` registra o limite pedido, nao garante disponibilidade ate ele. O exportador calcula o fim comum como o menor entre o fim do CDI, o fim da PTAX e o fim solicitado.

A UI usa `coverage.end_date` como fim padrao e para o indicador de cobertura, mas permite entrada ate `coverage.requested_end_date` quando presente; as regras de fallback continuam limitando o calculo. Confira as datas efetivas antes de interpretar resultados apos o fim comum.

Para diagnosticar uma publicacao antiga, comece pelo manifesto e depois examine os limites por serie no dataset. Contagens ou geracao recentes, isoladamente, nao comprovam dados recentes. O procedimento esta em [publicacao](publicacao.md#diagnostico-e-recuperacao).
