# Arquivo Historico

Esta pasta guarda materiais que ajudam a entender decisoes anteriores do projeto, mas que nao fazem parte do fluxo operacional atual do MVP.

## Itens arquivados

- `frontpage_formatacao.md`: registro de parametros de frontpage usado como apoio para uma avaliacao visual/redesign. A implementacao ativa continua em `app.py` e `armadilha_cdi/frontpage_texts.py`.
- `plano-publicacao-estatica.md`: plano de migracao para Cloudflare Pages. Foi arquivado depois da publicacao estatica passar a ser a superficie publica principal.

## Controles removidos da base ativa

Em maio de 2026, a base deixou de versionar controles locais de agentes e editor que nao sao necessarios para rodar, testar ou publicar o produto:

- `.agents/skills/supabase-postgres-best-practices/`;
- `.claude/skills/supabase-postgres-best-practices`;
- `skills-lock.json`;
- `.vscode/settings.json`.

O motivo foi manter o repositorio focado no produto: codigo Python, testes, documentacao, migracao Supabase e plano de publicacao estatica. As decisoes relevantes de Postgres/Supabase permanecem consolidadas em `docs/publicacao.md`, `docs/arquitetura.md` e `supabase/migrations/`.
