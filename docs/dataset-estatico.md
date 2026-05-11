# Dataset Estatico de Mercado

O dataset estatico transporta dados oficiais pre-gerados para o navegador. Ele nao contem segredos e nao deve depender de consulta ao Banco Central durante a interacao do usuario.

## Decisao de Granularidade

A versao inicial usa arquivo unico. O historico diario de CDI e PTAX desde 1994 cabe em um JSON simples e evita complexidade prematura no carregamento. A decisao deve ser reavaliada se o arquivo comprimido deixar de ser confortavel para primeiro carregamento em rede comum.

## `public/data/market-data.latest.json`

Schema versionado:

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

O manifesto existe para a pagina e para operacao conferirem rapidamente qual dataset esta publicado sem carregar outros metadados.

## Validacoes Obrigatorias

- Todas as datas devem estar em `YYYY-MM-DD`.
- `generated_at` deve terminar com `Z`.
- Taxas e cotacoes devem ser numeros finitos.
- `cdi_rates` e `usd_rates` nao podem estar vazios.
- A cobertura deve respeitar `1994-07-01` como minimo.
- `coverage.end_date` nao pode ultrapassar os limites reais das series.
- O arquivo publicado nao pode conter URLs de credenciais, tokens ou strings de conexao.
