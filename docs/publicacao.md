# Publicacao

Este projeto tem dois caminhos operacionais:

- publicacao estatica em Cloudflare Pages, recomendada para a superficie publica quando validada;
- MVP Streamlit, mantido como referencia funcional e ferramenta local/admin.

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

O caminho padrao usa cache JSON local em `cache/` e nao exige segredos. Se o exportador for configurado para usar Supabase/Postgres no CI, guarde `SUPABASE_DATABASE_URL` somente em secrets do GitHub Actions ou da plataforma de deploy.

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

### Recuperacao em caso de falha de dados

- Se o workflow diario falhar porque o Banco Central ainda nao publicou dados recentes, a pagina publicada continua usando o ultimo JSON valido.
- Rode `Update static market data` manualmente no GitHub Actions depois da publicacao oficial.
- Se a validacao cruzada falhar, nao force o commit do dataset; investigue primeiro diferencas entre `public/assets/calculations.js` e `armadilha_cdi/services/calculations.py`.
- Se o cache local do CI ficar corrompido, limpe o cache do workflow e execute novamente. O exportador reconstruira os arquivos a partir do Banco Central.

## Publicacao do MVP Streamlit

Este e o caminho recomendado para publicar o MVP gratuitamente, mantendo o cache persistente fora do filesystem efemero do servidor.

### Arquitetura de publicacao

- App: Streamlit Community Cloud.
- Codigo: repositorio GitHub publico.
- Cache persistente: Supabase Free, usando o Postgres do projeto.
- Conexao: Shared Pooler / Transaction pooler, com `sslmode=require`.
- Entrada da aplicacao: `app.py`.
- Dependencias Python: `requirements.txt`.
- Segredos: painel de Secrets do Streamlit Cloud.

O cache JSON local continua sendo o padrao para desenvolvimento. Em publicacao, use `MARKET_DATA_CACHE_BACKEND=supabase` para evitar perda de cache entre reinicios e reduzir chamadas repetidas ao Banco Central.

O backend Postgres usa `UPSERT` atomico e desativa prepared statements na conexao (`prepare_threshold=None`), o que combina com o transaction pooler do Supabase.

### Checklist antes do deploy

1. Rode a suite de testes:

```bash
python3 -m unittest discover -s tests -v
```

2. Depois do push para o GitHub, confirme que o workflow `Tests` passou.

3. Confira a sujeira local e garanta que `cache/`, `.streamlit/`, `__pycache__/` e `.pytest_cache/` nao serao versionados:

```bash
git status --short
git ls-files cache .streamlit __pycache__ .pytest_cache
```

4. Crie ou escolha um projeto Supabase Free.

5. Pegue a connection string Postgres do Supabase. Para Streamlit Cloud, prefira `Direct > Shared Pooler > Transaction pooler`, com porta `6543` e `sslmode=require`.

6. Opcionalmente, antes do deploy, crie o schema pelo SQL Editor do Supabase usando `supabase/migrations/20260501000000_create_market_rates.sql`. O app tambem cria a tabela automaticamente se ela ainda nao existir.

7. No Streamlit Community Cloud, crie o app apontando para:

- repository: este repositorio no GitHub;
- branch: branch de publicacao;
- main file path: `app.py`;
- Python: 3.12.

8. Cole os secrets no painel do Streamlit Cloud, usando `docs/streamlit-secrets.example.toml` como base:

```toml
MARKET_DATA_CACHE_BACKEND = "supabase"
SUPABASE_DATABASE_URL = "postgresql://..."
SUPABASE_CACHE_TABLE = "market_rates"
```

9. Acesse o app publicado e rode uma consulta curta, por exemplo os ultimos 12 meses.

### Preaquecimento do cache Supabase

O app cria automaticamente a tabela `market_rates` se ela nao existir. A migracao em `supabase/migrations/` existe para deixar o schema reproduzivel e incluir ajustes especificos do Supabase, como RLS ligada e acesso anonimo revogado. Antes de divulgar o link, preaqueca o cache para reduzir latencia da primeira visita:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
SUPABASE_CACHE_TABLE="market_rates" \
python3 scripts/sync_market_data.py --start 1994-07-01
```

Se quiser comecar mais leve no primeiro deploy, sincronize uma janela menor:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
SUPABASE_CACHE_TABLE="market_rates" \
python3 scripts/sync_market_data.py --start 2020-01-01
```

Depois, rode a janela historica completa em um momento de menor pressa.

### Validacao funcional pos-deploy

Teste estes casos no app publicado:

- periodo recente com datas em dias uteis;
- periodo em que inicio ou fim cai em fim de semana;
- periodo com inicio em `01/07/1994`;
- periodo longo, para confirmar que o cache Supabase esta sendo usado.

O esperado e que a UI mostre claramente o periodo efetivo de mercado e quando a PTAX usada nao coincide com a data solicitada.

### Operacao continua

Atualize o cache de tempos em tempos fora da requisicao do usuario:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
SUPABASE_CACHE_TABLE="market_rates" \
python3 scripts/sync_market_data.py --start 2024-01-01
```

No MVP gratuito, essa rotina pode ser manual. Se o app ganhar uso recorrente, vale agendar a sincronizacao diaria em GitHub Actions, cron externo ou outro executor gratuito/conveniente.

### Cuidados

- Nunca commite `SUPABASE_DATABASE_URL` real.
- Nao use o backend JSON como escolha principal em publicacao.
- Nao use `Framework`, `anon key`, `service_role key` ou Project URL no Streamlit; este app precisa da connection string Postgres.
- Se o Supabase Free pausar por inatividade, reative o projeto e rode novamente o sync.
- Se a primeira consulta publicada ficar lenta, rode o preaquecimento do cache e teste de novo.
- Se o Banco Central estiver indisponivel, o app so conseguira responder janelas ja cobertas pelo cache.
