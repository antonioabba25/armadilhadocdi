> Arquivado em 09/11/2026. Este guia pressupunha Cloudflare Pages. A publicacao observada usa Cloudflare Workers; consulte o [guia vigente](../publicacao.md). Configuracoes abaixo sao historicas.

# Publicacao

Este projeto tem uma unica superficie publicada: a versao estatica em Cloudflare Pages.

## Publicacao estatica em Cloudflare Pages

A versao estatica fica em `public/` e usa dados pre-gerados em `public/data/`. O navegador carrega `market-data.latest.json`, calcula localmente e nao consulta o Banco Central durante a interacao do usuario.

### Build e saida

- Framework preset: nenhum, static site ou equivalente.
- Build command recomendado:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
npm run test:js
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

- Output directory: `public`.

Se o deploy consumir os arquivos ja commitados em `public/data/`, o build command pode ser reduzido a testes e validacao. O workflow `.github/workflows/update-static-market-data.yml` ja atualiza diariamente o dataset e commita apenas `public/data/market-data.latest.json` e `public/data/market-data.manifest.json`.

### Variaveis e segredos

O caminho padrao usa cache JSON local em `cache/` e nao exige segredos.

Nao publique credenciais dentro de `public/` nem em arquivos versionados. O exportador valida o dataset para bloquear texto com aparencia de segredo antes da escrita.

### Checklist de preview

1. Rode os testes locais:

```bash
python3 -m unittest discover -s tests -v
npm run test:js
```

2. Gere ou atualize os dados:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 scripts/validate_static_reference_cases.py
```

3. Sirva a pasta `public/` localmente:

```bash
python3 -m http.server 8000 --directory public
```

4. Acesse `http://localhost:8000`, teste um periodo recente, um historico e um com fim de semana.

5. No Cloudflare Pages, confira se `/data/market-data.latest.json` e `/data/market-data.manifest.json` respondem em navegador anonimo.

6. Confirme que a tela mostra a data de ultima geracao, a cobertura disponivel e avisos quando a PTAX usada difere da data efetiva.

### Operacao continua

O workflow `Update static market data` roda em dias uteis e pode ser acionado manualmente no GitHub Actions. Ele:

- restaura o cache local do workflow;
- instala as dependencias Python;
- roda testes Python e JavaScript;
- exporta o dataset estatico;
- valida equivalencia Python/JavaScript;
- commita somente os arquivos de `public/data/` quando houver alteracao.

### Recuperacao em caso de falha de dados

- Se o workflow diario falhar porque o Banco Central ainda nao publicou dados recentes, a pagina publicada continua usando o ultimo JSON valido.
- Rode `Update static market data` manualmente depois da publicacao oficial dos dados.
- Se a validacao cruzada falhar, nao force o commit do dataset; investigue primeiro diferencas entre `public/assets/calculations.js` e `armadilha_cdi/services/calculations.py`.
- Se o cache local do CI ficar corrompido, limpe o cache do workflow e execute novamente. O exportador reconstruira os arquivos a partir do Banco Central.
