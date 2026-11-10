# Plano de Publicacao Estatica em Cloudflare Pages

Este arquivo e um registro historico da migracao para a publicacao estatica.

## Resultado consolidado

- `public/` passou a ser a superficie publica do produto.
- O calculo financeiro foi portado para JavaScript puro em `public/assets/calculations.js`.
- A apresentacao e o grafico ficaram em `public/assets/presentation.js` e `public/assets/app.js`.
- O dataset oficial passou a ser versionado em `public/data/`.
- `.github/workflows/update-static-market-data.yml` passou a atualizar diariamente os arquivos de dados.
- `scripts/validate_static_reference_cases.py` passou a validar a equivalencia entre JavaScript e `armadilha_cdi/services/calculations.py`.

## Decisoes preservadas

- A pagina publicada nao consulta o Banco Central durante a interacao do usuario.
- O dataset publicado deve conter somente CDI SGS/BCB serie `12` e USD/BRL PTAX venda.
- O schema do dataset deve ser validado antes da escrita.
- O dataset nao pode conter texto com aparencia de segredo.
- Falha de atualizacao diaria nao deve derrubar a pagina ja publicada; ela continua usando o ultimo JSON valido.
- A metrica central permanece `real_usd_return_percentage`.

## Estado

Migracao concluida. Este documento nao e roteiro ativo; consulte o [mapa de contexto vigente](../README.md) para operacao atual.
