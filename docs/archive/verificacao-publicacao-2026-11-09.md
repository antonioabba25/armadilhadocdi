# Verificacao da publicacao — 09/11/2026

Registro historico da inspecao realizada nesta data. Nao substitui monitoramento nem descreve necessariamente o estado futuro do site. Procedimento vigente: [publicacao](../publicacao.md).

## Origem e escopo

URL fornecida pelo usuario: https://tr.ee/wZrNxtCJ-c. O redirecionamento levou ao perfil Linktree, onde foi localizado o site https://armadilhadocdi.antonioabba.workers.dev/.

Inspecao interativa no Firefox desktop, requisicoes HTTP dos arquivos publicos, testes locais e comparacao Python/JavaScript com o dataset publicado. Nao houve alteracao do produto, dos dados ou da hospedagem. Layout em celular nao foi verificado.

## Resultados

- HTML, CSS, `app.js`, `calculations.js`, `presentation.js` e os dois JSON retornaram HTTP 200 com tipos de conteudo adequados.
- HTML/CSS/JS publicados eram identicos aos arquivos locais examinados; os dados locais estavam atrasados em relacao a producao.
- Analise padrao, recálculo e grafico com as tres series funcionaram.
- Inicio em 01/11/2025 (sabado) foi resolvido para 31/10/2025 com aviso.
- Inicio em 01/07/1994 foi resolvido para 04/07/1994 com aviso.
- Periodo invertido gerou mensagem clara; valor zero foi bloqueado pela validacao do formulario. Recarregar restaurou a analise padrao.
- 38 testes Python, 13 testes JS e 10 casos de paridade passaram. O comparador tambem passou com o dataset baixado da publicacao.

Exemplo conferido com o nucleo Python: R$ 1.000,00 entre 30/10/2025 e 30/10/2026 → R$ 1.143,12, CDI +14,31%, USD inicial US$ 185,70, USD final US$ 210,86, variacao em USD +13,55%, 250 dias de CDI.

## Dados observados e pendencia

| Campo | Valor observado |
| --- | --- |
| Geracao UTC | `2026-11-07T02:09:22Z` |
| Geracao em Sao Paulo | 06/11/2026, 23h09 |
| Cobertura comum | 01/07/1994 a 30/10/2026 |
| Ultimo CDI | 05/11/2026 |
| Ultima PTAX | 30/10/2026 |
| Contagens | 8.118 CDI; 8.113 USD/BRL |

A causa da defasagem da PTAX nao foi investigada ate sua conclusao. Uma exportacao bem-sucedida nao comprova frescor das series.

Evidencias externas consultadas: [manifesto](https://armadilhadocdi.antonioabba.workers.dev/data/market-data.manifest.json), [dataset](https://armadilhadocdi.antonioabba.workers.dev/data/market-data.latest.json), [execucao de atualizacao](https://github.com/antonioabba25/armadilhadocdi/actions/runs/42327750524) e [check do Cloudflare Workers](https://github.com/antonioabba25/armadilhadocdi/runs/128267337751). Os URLs dos dados sao mutaveis; os valores acima registram a observacao, nao um snapshot imutavel dos JSON.
