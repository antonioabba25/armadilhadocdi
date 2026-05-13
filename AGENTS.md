# Armadilha do CDI

## Leitura correta do produto

Este projeto nao e uma calculadora generica de rendimento CDI. Ele responde:

> Se um capital ficou aplicado em CDI entre duas datas, a posicao relativa em dolar melhorou, piorou ou apenas pareceu ter melhorado em reais?

Toda tarefa futura deve preservar essa leitura. O resultado principal e a comparacao entre crescimento nominal em BRL e poder relativo em USD.

## Estado atual da base

O produto publico e exclusivamente a publicacao estatica em `public/`, preparada para Cloudflare Pages:

- entrada: `data inicial`, `data final`, `valor inicial investido` em BRL;
- dados: dataset JSON versionado em `public/data/`, com CDI diario do SGS/BCB serie `12` e USD/BRL PTAX venda;
- calculo: JavaScript puro no navegador, sem consulta ao Banco Central durante a interacao do usuario;
- saida: analise em tres perspectivas, separando capital em BRL pelo CDI, cambio USD/BRL e posicao equivalente em USD;
- grafico SVG comparativo com CDI acumulado, variacao do USD/BRL e variacao em USD;
- manutencao: `.github/workflows/update-static-market-data.yml` atualiza diariamente o dataset estatico;
- validacao cruzada: `scripts/validate_static_reference_cases.py` compara os resultados JavaScript com o nucleo Python.

O Python permanece na base como nucleo de calculo, integracao com dados oficiais, cache JSON local e ferramentas operacionais para gerar/validar o dataset estatico. Nao ha segunda pagina web publicada.

Os scripts exploratorios antigos foram removidos da base ativa. As decisoes uteis deles foram consolidadas em `README.md`, `docs/metodologia.md`, `docs/arquitetura.md` e neste arquivo. Nao recrie notebook/script exploratorio como dependencia do MVP; implemente mudancas nos modulos de producao e cubra com testes.

## Publicacao estatica concluida

O plano de migracao para Cloudflare Pages foi concluido e arquivado em `docs/archive/plano-publicacao-estatica.md`.

Quando a tarefa mencionar Cloudflare Pages, pagina estatica, calculo no navegador, exportacao de dados, dataset JSON ou GitHub Actions de atualizacao diaria, trate `public/` como superficie unica de publicacao e preserve a equivalencia com `armadilha_cdi/services/calculations.py`. Consulte o plano arquivado apenas como historico de decisoes, nao como roteiro ativo.

## Arquitetura ativa

```text
public/
  index.html
  assets/
    app.js
    calculations.js
    presentation.js
    styles.css
  data/
    market-data.latest.json
    market-data.manifest.json
armadilha_cdi/
  config.py
  exceptions.py
  models.py
  services/
    cache.py
    calculations.py
    data_providers.py
docs/
scripts/
tests/
```

Responsabilidades:

- `public/index.html`: pagina estatica publicada.
- `public/assets/calculations.js`: regra financeira portada para JavaScript puro.
- `public/assets/presentation.js`: derivados de apresentacao para BRL, USD/BRL e posicao em USD.
- `public/assets/app.js`: UI estatica, renderizacao da analise e grafico.
- `public/data/`: dataset estatico usado pelo navegador.
- `armadilha_cdi/services/data_providers.py`: consultas ao Banco Central e sincronizacao com cache JSON local.
- `armadilha_cdi/services/cache.py`: contrato de cache, backend JSON local, normalizacao e merge.
- `armadilha_cdi/services/calculations.py`: regra financeira principal e fallback de cotacao.
- `armadilha_cdi/models.py`: dataclasses de troca entre camadas.
- `armadilha_cdi/exceptions.py`: erros de dominio e dados de mercado.
- `scripts/sync_market_data.py`: sincronizacao manual/agendavel do cache JSON local.
- `scripts/export_static_market_data.py`: geracao e validacao do dataset estatico.
- `scripts/validate_static_reference_cases.py`: comparacao dos resultados Python e JavaScript em casos reais.
- `.github/workflows/update-static-market-data.yml`: atualizacao diaria do dataset estatico.
- `docs/archive/plano-publicacao-estatica.md`: plano historico da migracao para Cloudflare Pages.
- `docs/archive/`: materiais historicos uteis que nao fazem parte do fluxo operacional ativo.

## Regras de negocio que nao devem mudar sem decisao explicita

- Datas sem dado oficial sao resolvidas para a ultima data util disponivel.
- Na borda inicial do real, quando nao houver CDI anterior permitido, a data inicial pode ser resolvida para o primeiro CDI oficial disponivel dentro da tolerancia de calendario.
- A data inicial deve ser 01/07/1994 ou posterior; dados anteriores a entrada em circulacao do real brasileiro nao devem ser usados como fallback inicial.
- A janela do CDI e `data_inicial_efetiva <= data < data_final_efetiva`.
- O CDI e acumulado diariamente com `fator *= 1 + taxa_diaria / 100`.
- USD/BRL usa PTAX de venda.
- Se nao houver PTAX na data solicitada, usar a cotacao anterior mais proxima.
- O fallback de USD/BRL e limitado por `MAX_USD_FALLBACK_DAYS`, hoje 15 dias.
- A metrica central e `real_usd_return_percentage`.
- A UI deve informar quando a data efetiva da cotacao difere da data solicitada.
- Calculos, graficos e visualizacoes devem considerar apenas dias uteis presentes nas series oficiais.

## Contrato minimo do calculo

A funcao central e:

```python
calculate_result(
    start_date: date,
    end_date: date,
    initial_brl: float,
    cdi_rates: dict[str, float],
    usd_rates: dict[str, float],
) -> CalculationResult
```

Campos essenciais do resultado:

- `initial_brl`;
- `final_brl`;
- `cdi_percentage`;
- `effective_start_date`;
- `effective_end_date`;
- `initial_usdbrl`;
- `final_usdbrl`;
- `initial_usd`;
- `final_usd_with_cdi`;
- `real_usd_return_percentage`;
- `initial_fx_date`;
- `final_fx_date`;
- `cdi_days_used`.

## Comandos uteis

Rodar testes:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
```

Servir a pagina estatica localmente:

```bash
python3 -m http.server 8000 --directory public
```

Preaquecer/sincronizar cache JSON local:

```bash
python3 scripts/sync_market_data.py --start 2020-01-01
```

Gerar e validar dataset estatico:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

Checar arquivos rastreados e sujeira local:

```bash
git status --short
git ls-files
```

## Diretrizes para futuras tarefas

- Prefira mudar `armadilha_cdi/services/calculations.py` quando a regra financeira mudar.
- Prefira mudar `armadilha_cdi/services/data_providers.py` quando a origem ou sincronizacao de dados mudar.
- Prefira mudar `armadilha_cdi/services/cache.py` quando a persistencia local, lock ou escrita do cache mudar.
- Preserve o backend JSON local como caminho operacional dos scripts.
- Para a publicacao estatica, preserve a equivalencia testavel entre o nucleo Python e o calculo JavaScript.
- Para datasets estaticos, nao exponha segredos, nao consulte o Banco Central durante a interacao do usuario e valide o schema antes de publicar.
- Nao adicione dependencias para resolver algo que a biblioteca padrao ja resolva bem.
- Preserve mensagens de erro claras para datas invalidas, valor inicial invalido e ausencia de dados.
- Ao alterar regra de calculo, atualize `docs/metodologia.md`, `README.md` e os testes.
- Ao alterar arquitetura ou responsabilidades, atualize `docs/arquitetura.md` e este arquivo.
- Arquivos gerados como `cache/`, `__pycache__/`, `.pytest_cache/` e controles locais de agente/editor nao devem ser versionados.
- Controles locais de agente/editor, como `.agents/`, `.claude/`, `.vscode/` e `skills-lock.json`, ficam fora da base ativa salvo decisao explicita.

## Escopo futuro, mas fora do MVP atual

- IPCA como serie opcional no grafico.
- Inflacao americana como camada adicional de poder de compra em USD.
- Endpoint HTTP fora da publicacao estatica.
- Cache em storage de objetos ou servico gerenciado.

Esses temas podem ser implementados depois, mas nao devem complicar o fluxo minimo `CDI + USD/BRL` sem necessidade de produto.
