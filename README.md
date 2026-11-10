# Armadilha do CDI

Se um capital ficou aplicado em CDI entre duas datas, sua posicao relativa em dolar melhorou, piorou ou apenas pareceu melhorar em reais?

O app compara tres perspectivas: capital em BRL pelo CDI, cambio USD/BRL e posicao equivalente em USD. O grafico apresenta CDI acumulado, variacao cambial e variacao em USD. As taxas equivalentes mensal/anual contextualizam o periodo historico, sem prever retornos.

**Site:** https://armadilhadocdi.antonioabba.workers.dev/

**Documentacao:** [mapa de contexto](docs/README.md) · [instrucoes para agentes](AGENTS.md)

## Funcionamento

- A publicacao estatica usa somente `public/`, atualmente servida pelo Cloudflare Workers.
- O navegador carrega o dataset JSON e calcula localmente, sem consultar o Banco Central.
- As fontes sao CDI diario SGS/BCB serie 12 e USD/BRL PTAX venda.
- Python mantem o nucleo de referencia, integracao com dados oficiais, cache JSON e exportacao.
- GitHub Actions agenda a atualizacao em dias de semana e valida a equivalencia Python/JavaScript.

A data inicial minima e 01/07/1994. O CDI acumula com inicio efetivo inclusivo e fim efetivo exclusivo. Datas sem observacao oficial sao ajustadas com avisos; detalhes em [metodologia e contrato](docs/metodologia.md).

## Desenvolvimento local

Requisitos: Python 3.12+ e Node.js compativel com `node --test` (CI usa Node 22).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m http.server 8000 --directory public
```

Abra http://localhost:8000. O site pode ser servido com os dados ja versionados; nao e necessario sincronizar o BCB para iniciar a interface.

Verificacoes:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
python3 scripts/validate_static_reference_cases.py
```

Geracao de dados, diagnostico de defasagem e verificacao do site: [guia operacional](docs/publicacao.md).

## Organizacao

| Caminho | Responsabilidade |
| --- | --- |
| `public/` | Artefato publicado: pagina, assets e dados |
| `armadilha_cdi/` | Nucleo Python, modelos, integracao BCB e cache |
| `scripts/` | Sincronizacao, exportacao e validacao cruzada |
| `tests/` | Testes Python/JavaScript e periodos de referencia |
| `.github/workflows/` | Testes e atualizacao de dados |
| `docs/` | Documentacao vigente, com [indice por tarefa](docs/README.md) |
| `docs/archive/` | Documentos superados e evidencias historicas datadas |

## Limites e estado observado

A metrica `real_usd_return_percentage` expressa variacao da posicao equivalente em USD. O MVP nao considera IPCA, inflacao americana, impostos, taxas, spread cambial, IOF ou custos operacionais. A PTAX e uma referencia oficial, nao uma cotacao de operacao individual. O app nao apresenta conclusao de poder de compra real.

Na [verificacao de 09/11/2026](docs/archive/verificacao-publicacao-2026-11-09.md), o site funcionou nos cenarios desktop testados; a cobertura comum terminava em 30/10/2026 e exigia investigacao. Esse registro e uma fotografia da data, nao um indicador ao vivo. Consulte o manifesto publicado e o [guia operacional](docs/publicacao.md) para verificar o estado atual.
