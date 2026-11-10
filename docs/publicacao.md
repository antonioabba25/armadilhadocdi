# Publicacao e Operacao

## Destino e responsabilidades

- Site direto: https://armadilhadocdi.antonioabba.workers.dev/
- [Repositorio](https://github.com/antonioabba25/armadilhadocdi).
- [Atualizacao de dados](https://github.com/antonioabba25/armadilhadocdi/actions/workflows/update-static-market-data.yml).
- Artefato: somente `public/`, incluindo `assets/` e `data/`.

A hospedagem observada em 09/11/2026 usa Cloudflare Workers, com check `Workers Builds: armadilhadocdi`. A configuracao de deploy e mantida externamente; nao ha arquivo Wrangler versionado. Verifique o painel antes de alterar build, dominio ou bindings. O [guia antigo de Pages](archive/guia-cloudflare-pages.md) foi arquivado e nao descreve a configuracao atual.

O navegador calcula a partir de `data/market-data.latest.json`. O [manifesto publicado](https://armadilhadocdi.antonioabba.workers.dev/data/market-data.manifest.json) permite inspecao rapida de cobertura e contagens. Consulte o [schema](dataset-estatico.md) para distinguir geracao, periodo solicitado e datas realmente disponiveis.

## Validacao local

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
npm run test:js
python3 scripts/validate_static_reference_cases.py
python3 -m http.server 8000 --directory public
```

Abra http://localhost:8000. Teste periodo recente, historico desde 01/07/1994, fim de semana, periodo invertido e valor zero. Confira as tres perspectivas, o grafico, os avisos e os metadados. Os testes de texto da UI nao substituem a verificacao visual/interativa.

## Atualizacao de dados

Para sincronizar o cache manualmente:

```bash
python3 scripts/sync_market_data.py --start 2020-01-01
```

Para exportar toda a janela suportada e validar:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

A exportacao escreve os dois JSON versionados em `public/data/`; revise as alteracoes antes de commitar. `cache/` e apoio operacional local, com lock e escrita atomica, e nao deve ser publicado/versionado. A integracao BCB divide consultas longas de CDI e trata janelas oficialmente vazias; detalhes de implementacao em [arquitetura](arquitetura.md).

O [workflow](../.github/workflows/update-static-market-data.yml) tem agendamento `30 22 * * 1-5` (22h30 UTC, 19h30 em America/Sao_Paulo no fuso UTC-3) e acionamento manual. A execucao real pode atrasar. Ele restaura cache, instala dependencias, testa, exporta, valida equivalencia e commita apenas dataset/manifesto quando alterados.

## Verificacao da publicacao

1. Acesse o site direto e confirme que o carregamento termina e a analise padrao aparece.
2. Confira HTTP 200 e conteudo correto para pagina, CSS, tres modulos JS e ambos os JSON. Nao use somente `HEAD` para testar encurtadores; o link informado via Linktree exigiu `GET`.
3. Compare `generated_at`, `coverage.end_date`, `coverage.cdi_end_date` e `coverage.usd_end_date`. Geracao recente nao implica series recentes.
4. Compare a publicacao com o commit/dataset remoto esperado; a copia local pode estar atrasada.
5. Baixe o dataset publicado para um caminho temporario e rode `python3 scripts/validate_static_reference_cases.py --dataset CAMINHO_DO_JSON`. Isso compara as implementacoes locais com os dados publicados; para validar o codigo em producao, confirme tambem se os modulos JS publicados correspondem aos locais.
6. Teste os cenarios da validacao local no site. Para mudancas de layout, verifique desktop e celular. Confirme a recuperacao depois de uma entrada invalida.

## Diagnostico e recuperacao

| Sintoma | Investigacao |
| --- | --- |
| Site abre, mas dados estao antigos | Confira limites de cada serie, workflow, resposta BCB, cache e se o deploy incorporou o commit |
| Build/workflow verde, cobertura antiga | Sucesso tecnico nao garante frescor; identifique qual serie limita `coverage.end_date` |
| Interface presa no carregamento | Confira caminho e conteudo do JSON, status HTTP, schema e erros no navegador |
| Comparador diverge | Investigue nucleo Python/JS; nao force commit de dataset para contornar a falha |
| Cache corrompido | Limpe/reconstrua o cache operacional afetado e execute a exportacao novamente |
| BCB temporariamente indisponivel | Preserve o ultimo JSON valido; repita apos a normalizacao |

O caminho padrao dos scripts nao exige segredos; isso nao descreve as credenciais da infraestrutura de hospedagem. Nunca coloque credenciais em `public/` ou arquivos versionados. A exportacao valida schema e texto com aparencia de segredo.

## Pendencias observadas em 09/11/2026

A [verificacao datada](archive/verificacao-publicacao-2026-11-09.md) encontrou o site funcionando, com CDI ate 05/11 e PTAX ate 30/10, embora o arquivo tivesse sido gerado em 06/11. A causa da defasagem da PTAX nao foi determinada. Investigar provider/cache/fonte antes de atribuir causa ao BCB. A UI em celular ainda precisa ser verificada. Atualize esta secao quando houver nova evidencia; o relatorio historico deve manter sua data e escopo.
