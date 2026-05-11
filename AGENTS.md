# Armadilha do CDI

## Leitura correta do produto

Este projeto não é uma calculadora genérica de rendimento CDI. Ele responde:

> Se um capital ficou aplicado em CDI entre duas datas, a posição relativa em dólar melhorou, piorou ou apenas pareceu ter melhorado em reais?

Toda tarefa futura deve preservar essa leitura. O resultado principal é a comparação entre crescimento nominal em BRL e poder relativo em USD.

## Estado atual da base

O produto público atual é a publicação estática em `public/`, preparada para Cloudflare Pages:

- entrada: `data inicial`, `data final`, `valor inicial investido` em BRL;
- dados: dataset JSON versionado em `public/data/`, com CDI diário do SGS/BCB série `12` e USD/BRL PTAX venda;
- cálculo: JavaScript puro no navegador, sem consulta ao Banco Central durante a interação do usuário;
- saída: análise em três perspectivas, separando capital em BRL pelo CDI, câmbio USD/BRL e posição equivalente em USD;
- gráfico SVG comparativo com CDI acumulado, variação do USD/BRL e variação em USD;
- manutenção: `.github/workflows/update-static-market-data.yml` atualiza diariamente o dataset estático;
- validação cruzada: `scripts/validate_static_reference_cases.py` compara os resultados JavaScript com o núcleo Python.

O Streamlit continua na base como referência funcional, ferramenta local/admin e implementação Python pura:

- entrada: `data inicial`, `data final`, `valor inicial investido` em BRL;
- dados: CDI diário do SGS/BCB, série `12`;
- consultas longas de CDI ao SGS/BCB são fatiadas em janelas menores com pequeno delay entre requisições;
- dados: USD/BRL pela PTAX de venda via API Olinda/BCB;
- saída: resumo analítico e gráfico comparativo;
- cache configurável: JSON local em `cache/` para desenvolvimento, ou Postgres/Supabase para publicação;
- sincronização sob demanda busca apenas bordas ausentes quando o cache já cobre parte da janela;
- bordas curtas de CDI sem observações oficiais no SGS/BCB são tratadas como janelas vazias, não como falha fatal;
- cache local com lock por arquivo e escrita atômica; cache Postgres/Supabase com `UPSERT` transacional por série e data;
- sincronização operacional: `scripts/sync_market_data.py` para preaquecer/atualizar o cache fora da requisição do usuário.

Os scripts exploratórios antigos foram removidos da base ativa. As decisões úteis deles foram consolidadas em `README.md`, `docs/metodologia.md`, `docs/arquitetura.md` e neste arquivo. Não recrie notebook/script exploratório como dependência do MVP; implemente mudanças nos módulos de produção e cubra com testes.

## Publicação estática concluída

O plano de migração para Cloudflare Pages foi concluído e arquivado em `docs/archive/plano-publicacao-estatica.md`.

Quando a tarefa mencionar Cloudflare Pages, página estática, cálculo no navegador, exportação de dados, dataset JSON ou GitHub Actions de atualização diária, trate `public/` como superfície principal e preserve a equivalência com `armadilha_cdi/services/calculations.py`. Consulte o plano arquivado apenas como histórico de decisões, não como roteiro ativo.

## Arquitetura ativa

```text
app.py
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
    charts.py
    data_providers.py
docs/
scripts/
tests/
```

Responsabilidades:

- `app.py`: UI Streamlit, formulário, renderização de métricas, gráfico e mensagens.
- `armadilha_cdi/services/data_providers.py`: consultas ao Banco Central e sincronização com cache.
- `armadilha_cdi/services/cache.py`: contrato de cache, backend JSON local, backend Postgres/Supabase, normalização e merge.
- `armadilha_cdi/services/calculations.py`: regra financeira principal e fallback de cotação.
- `armadilha_cdi/services/charts.py`: séries derivadas para visualização.
- `armadilha_cdi/models.py`: dataclasses de troca entre camadas.
- `armadilha_cdi/exceptions.py`: erros de domínio e dados de mercado.
- `scripts/sync_market_data.py`: sincronização manual/agendável do cache.
- `scripts/export_static_market_data.py`: geração e validação do dataset estático.
- `scripts/validate_static_reference_cases.py`: comparação dos resultados Python e JavaScript em casos reais.
- `public/assets/calculations.js`: regra financeira portada para JavaScript puro.
- `public/assets/presentation.js`: derivados de apresentação para BRL, USD/BRL e posição em USD.
- `public/assets/app.js`: UI estática, renderização da análise e gráfico.
- `.github/workflows/update-static-market-data.yml`: atualização diária do dataset estático.
- `docs/archive/plano-publicacao-estatica.md`: plano histórico da migração para Cloudflare Pages.
- `docs/archive/`: materiais históricos úteis que não fazem parte do fluxo operacional ativo.

## Regras de negócio que não devem mudar sem decisão explícita

- Datas sem dado oficial são resolvidas para a última data útil disponível.
- Na borda inicial do real, quando não houver CDI anterior permitido, a data inicial pode ser resolvida para o primeiro CDI oficial disponível dentro da tolerância de calendário.
- A data inicial deve ser 01/07/1994 ou posterior; dados anteriores à entrada em circulação do real brasileiro não devem ser usados como fallback inicial.
- A janela do CDI é `data_inicial_efetiva <= data < data_final_efetiva`.
- O CDI é acumulado diariamente com `fator *= 1 + taxa_diaria / 100`.
- USD/BRL usa PTAX de venda.
- Se não houver PTAX na data solicitada, usar a cotação anterior mais próxima.
- O fallback de USD/BRL é limitado por `MAX_USD_FALLBACK_DAYS`, hoje 15 dias.
- A métrica central é `real_usd_return_percentage`.
- A UI deve informar quando a data efetiva da cotação difere da data solicitada.
- Cálculos, gráficos e visualizações devem considerar apenas dias úteis presentes nas séries oficiais.

## Contrato mínimo do cálculo

A função central é:

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

## Comandos úteis

Rodar testes:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
```

Rodar app:

```bash
streamlit run app.py
```

Preaquecer/sincronizar cache:

```bash
python3 scripts/sync_market_data.py --start 2020-01-01
```

Gerar e validar dataset estático:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

Preaquecer/sincronizar cache Supabase:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
python3 scripts/sync_market_data.py --start 2020-01-01
```

Checar arquivos rastreados e sujeira local:

```bash
git status --short
git ls-files
```

## Diretrizes para futuras tarefas

- Prefira mudar `armadilha_cdi/services/calculations.py` quando a regra financeira mudar.
- Prefira mudar `armadilha_cdi/services/data_providers.py` quando a origem ou sincronização de dados mudar.
- Prefira mudar `armadilha_cdi/services/cache.py` quando a persistência local, lock ou escrita do cache mudar.
- Preserve o backend JSON como padrão local e use `MARKET_DATA_CACHE_BACKEND=supabase` para publicação com Supabase/Postgres.
- Prefira mudar `armadilha_cdi/services/charts.py` quando a visualização precisar de novas séries derivadas.
- Prefira mudar `scripts/sync_market_data.py` quando o fluxo operacional de preaquecer/atualizar cache mudar.
- Mantenha `app.py` focado em interface; evite colocar regra financeira nele.
- Para a publicação estática, preserve a equivalência testável entre o núcleo Python e o cálculo JavaScript.
- Para datasets estáticos, não exponha segredos, não consulte o Banco Central durante a interação do usuário e valide o schema antes de publicar.
- Não adicione dependências para resolver algo que a biblioteca padrão ou pandas já resolvem bem.
- Preserve mensagens de erro claras para datas inválidas, valor inicial inválido e ausência de dados.
- Ao alterar regra de cálculo, atualize `docs/metodologia.md`, `README.md` e os testes.
- Ao alterar arquitetura ou responsabilidades, atualize `docs/arquitetura.md` e este arquivo.
- Arquivos gerados como `cache/`, `__pycache__/`, `.pytest_cache/` e `.streamlit/` não devem ser versionados.
- Controles locais de agente/editor, como `.agents/`, `.claude/`, `.vscode/` e `skills-lock.json`, ficam fora da base ativa salvo decisão explícita.

## Escopo futuro, mas fora do MVP atual

- IPCA como série opcional no gráfico.
- Inflação americana como camada adicional de poder de compra em USD.
- Endpoint HTTP fora do Streamlit.
- Cache em storage de objetos ou serviço gerenciado diferente do Supabase/Postgres.

Esses temas podem ser implementados depois, mas não devem complicar o fluxo mínimo `CDI + USD/BRL` sem necessidade de produto.
