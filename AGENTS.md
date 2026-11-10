# Armadilha do CDI — instrucoes de trabalho

## Contexto minimo

O produto compara crescimento nominal em BRL pelo CDI com a posicao equivalente em USD entre duas datas. A metrica central e `real_usd_return_percentage`; ela nao mede inflacao nem poder de compra real em USD.

A unica superficie publica e `public/`, com JavaScript puro e JSON versionado. O Python fornece a referencia financeira, integracao BCB, cache e ferramentas operacionais. A publicacao verificada em 09/11/2026 usa Cloudflare Workers: https://armadilhadocdi.antonioabba.workers.dev/.

## Leitura por tarefa

Leia este arquivo e depois apenas o ramo necessario do [mapa de contexto](docs/README.md). Evite carregar toda a documentacao ou os JSON de mercado para tarefas que nao dependem deles.

| Tarefa | Documento principal | Entrada no codigo |
| --- | --- | --- |
| Regra financeira, datas, fallback | [Metodologia e contrato](docs/metodologia.md) | `armadilha_cdi/services/calculations.py`, `public/assets/calculations.js` |
| UI, apresentacao, grafico | [Arquitetura](docs/arquitetura.md) | `public/index.html`, `public/assets/` |
| BCB, sincronizacao, cache | [Arquitetura](docs/arquitetura.md) e [fontes](docs/referencias.md) | `armadilha_cdi/services/data_providers.py`, `cache.py` |
| Dataset, exportacao | [Schema](docs/dataset-estatico.md) | `scripts/export_static_market_data.py` |
| Publicacao, CI, dados defasados | [Operacao](docs/publicacao.md) | `.github/workflows/`, `public/data/market-data.manifest.json` |

O [arquivo historico](docs/archive/README.md) so deve ser consultado para investigar decisoes antigas. Nao e roteiro ativo.

## Invariantes

- Data inicial >= `1994-07-01`; nunca usar fallback anterior ao real.
- Datas sem CDI usam o ultimo ponto oficial anterior dentro da tolerancia. Na borda inicial do real, pode ser usado o primeiro CDI oficial disponivel dentro da tolerancia.
- Janela CDI: `data_inicial_efetiva <= data < data_final_efetiva`.
- Acumulo: `fator *= 1 + taxa_diaria / 100`.
- USD/BRL usa PTAX venda na data efetiva de mercado; se ausente, usa a anterior mais proxima, limitada a 15 dias (`MAX_USD_FALLBACK_DAYS`).
- UI informa ajustes do periodo e datas efetivas de PTAX. Calculo e grafico usam apenas pontos oficiais da serie CDI.
- Preserve a equivalencia testavel entre Python e JavaScript.
- O navegador nao consulta o Banco Central durante a interacao. Valide o schema antes de publicar dados e nao exponha segredos.

## Execucao e verificacao

```bash
python3 -m unittest discover -s tests -v
npm run test:js
python3 scripts/validate_static_reference_cases.py
python3 -m http.server 8000 --directory public
```

O comparador usa o dataset local, que pode diferir da publicacao. Para operacao de dados e verificacao remota, siga [publicacao](docs/publicacao.md).

## Manutencao

- Mude a regra financeira primeiro no nucleo Python e mantenha o JavaScript equivalente; atualize metodologia, testes e o resumo do README quando afetado.
- Origem/sincronizacao pertence a `data_providers.py`; persistencia, lock e escrita atomica pertencem a `cache.py`. Preserve o backend JSON local dos scripts.
- Preserve erros claros para datas, valores e ausencia de dados. Nao recrie scripts exploratorios como dependencia do MVP.
- Nao adicione dependencias quando a biblioteca padrao resolver bem.
- Mudancas de responsabilidades devem atualizar arquitetura, mapa de contexto e estas instrucoes quando necessario.
- Cada assunto tem um documento principal no mapa; prefira links a copiar regras. Ao substituir um documento, arquive com motivo, data e link para o sucessor; corrija referencias ativas.
- Observacoes de producao devem ter data e evidencia. Build bem-sucedido nao comprova cobertura recente nem funcionamento da UI.
- `cache/`, `__pycache__/`, `.pytest_cache/`, `.agents/`, `.claude/`, `.vscode/` e `skills-lock.json` ficam fora da base versionada, salvo decisao explicita.

## Fora do MVP

IPCA, inflacao americana, impostos, taxas, spread, IOF, endpoint HTTP e storage gerenciado nao integram o fluxo atual. Nao acrescente essas camadas sem necessidade explicita de produto.
