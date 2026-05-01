# Publicacao do MVP

Este e o caminho recomendado para publicar o MVP gratuitamente, mantendo o cache persistente fora do filesystem efemero do servidor.

## Arquitetura de publicacao

- App: Streamlit Community Cloud.
- Codigo: repositorio GitHub publico.
- Cache persistente: Supabase Free, usando o Postgres do projeto.
- Conexao: Shared Pooler / Transaction pooler, com `sslmode=require`.
- Entrada da aplicacao: `app.py`.
- Dependencias Python: `requirements.txt`.
- Segredos: painel de Secrets do Streamlit Cloud.

O cache JSON local continua sendo o padrao para desenvolvimento. Em publicacao, use `MARKET_DATA_CACHE_BACKEND=supabase` para evitar perda de cache entre reinicios e reduzir chamadas repetidas ao Banco Central.

O backend Postgres usa `UPSERT` atomico e desativa prepared statements na conexao (`prepare_threshold=None`), o que combina com o transaction pooler do Supabase.

## Checklist antes do deploy

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

## Preaquecimento do cache Supabase

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

## Validacao funcional pos-deploy

Teste estes casos no app publicado:

- periodo recente com datas em dias uteis;
- periodo em que inicio ou fim cai em fim de semana;
- periodo com inicio em `01/07/1994`;
- periodo longo, para confirmar que o cache Supabase esta sendo usado.

O esperado e que a UI mostre claramente o periodo efetivo de mercado e quando a PTAX usada nao coincide com a data solicitada.

## Operacao continua

Atualize o cache de tempos em tempos fora da requisicao do usuario:

```bash
MARKET_DATA_CACHE_BACKEND=supabase \
SUPABASE_DATABASE_URL="postgresql://..." \
SUPABASE_CACHE_TABLE="market_rates" \
python3 scripts/sync_market_data.py --start 2024-01-01
```

No MVP gratuito, essa rotina pode ser manual. Se o app ganhar uso recorrente, vale agendar a sincronizacao diaria em GitHub Actions, cron externo ou outro executor gratuito/conveniente.

## Cuidados

- Nunca commite `SUPABASE_DATABASE_URL` real.
- Nao use o backend JSON como escolha principal em publicacao.
- Nao use `Framework`, `anon key`, `service_role key` ou Project URL no Streamlit; este app precisa da connection string Postgres.
- Se o Supabase Free pausar por inatividade, reative o projeto e rode novamente o sync.
- Se a primeira consulta publicada ficar lenta, rode o preaquecimento do cache e teste de novo.
- Se o Banco Central estiver indisponivel, o app so conseguira responder janelas ja cobertas pelo cache.
