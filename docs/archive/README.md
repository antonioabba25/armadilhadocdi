# Arquivo Historico

Esta pasta guarda materiais que ajudam a entender decisoes anteriores do projeto, mas que nao fazem parte do fluxo operacional atual do MVP.

## Itens arquivados

- `plano-publicacao-estatica.md`: plano de migracao para Cloudflare Pages. Foi arquivado depois da publicacao estatica passar a ser a superficie publica principal.

## Controles removidos da base ativa

Em maio de 2026, a base deixou de versionar controles locais de agentes e editor que nao sao necessarios para rodar, testar ou publicar o produto:

- `skills-lock.json`;
- `.vscode/settings.json`.

O motivo foi manter o repositorio focado no produto: codigo Python, testes, documentacao e publicacao estatica.
