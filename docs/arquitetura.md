# Arquitetura

## Visao geral

O projeto foi organizado para manter a regra financeira desacoplada da interface estatica. A ideia central e simples: a camada de apresentacao pode evoluir, mas a logica que responde se houve ganho ou perda relativa em dolar precisa continuar previsivel e testavel.

A base ativa nao depende mais de scripts exploratorios nem de runtime web Python. A memoria tecnica da fase inicial foi consolidada em `README.md`, `AGENTS.md` e nos documentos desta pasta.

## Camadas do projeto

### Publicacao estatica

- `public/index.html`
- `public/assets/app.js`
- `public/assets/calculations.js`
- `public/assets/presentation.js`
- `public/assets/styles.css`
- `public/data/market-data.latest.json`
- `public/data/market-data.manifest.json`

Responsabilidades:

- carregar o JSON estatico de mercado;
- validar entradas no navegador;
- executar a regra financeira em JavaScript puro;
- renderizar resumo, avisos de fallback e grafico SVG responsivo;
- exibir a data de ultima geracao e a cobertura publicada;
- manter a pagina publica sem processo servidor e sem chamadas ao Banco Central durante a interacao do usuario.

### Integracao com dados de mercado

- `armadilha_cdi/services/data_providers.py`

Responsabilidades:

- consultar CDI no Banco Central;
- consultar PTAX USD/BRL no Banco Central;
- sincronizar dados com o cache JSON local;
- buscar apenas as bordas ausentes quando o cache ja cobre parte da janela;
- tratar bordas de CDI sem observacoes oficiais como janelas vazias quando o SGS nao retorna dados;
- devolver um `MarketDataBundle` pronto para a camada de calculo e para a exportacao estatica.

### Cache

- `armadilha_cdi/services/cache.py`

Responsabilidades:

- definir o contrato comum de persistencia de series;
- persistir series em arquivos JSON;
- carregar historico ja existente;
- fazer merge incremental com novos dados;
- proteger load/merge/save com lock por arquivo;
- gravar por substituicao atomica para evitar JSON parcial;
- evitar recaptura completa do historico a cada execucao.

O cache local em `cache/` e adequado para desenvolvimento, testes operacionais e geracao do dataset publicado. Ele nao faz parte do artefato servido ao usuario final.

### Sincronizacao operacional

- `scripts/sync_market_data.py`
- `scripts/export_static_market_data.py`
- `.github/workflows/update-static-market-data.yml`

Responsabilidades:

- preaquecer ou atualizar o cache fora do uso do usuario;
- permitir execucao manual ou agendada;
- exportar `public/data/market-data.latest.json` e `public/data/market-data.manifest.json`;
- validar schema, cobertura e ausencia de texto com aparencia de segredo antes de publicar;
- atualizar diariamente os dados estaticos por GitHub Actions.

### Regra de negocio

- `armadilha_cdi/services/calculations.py`

Responsabilidades:

- validar entradas de dominio;
- impedir periodos iniciados antes da entrada em circulacao do real brasileiro, em 01/07/1994;
- resolver datas solicitadas para dias uteis oficiais;
- resolver a borda inicial do real para o primeiro CDI oficial disponivel quando nao ha CDI anterior permitido;
- aplicar a janela oficial do CDI sobre o periodo efetivo;
- resolver cotacoes com fallback;
- calcular BRL final, USD inicial, USD final e rentabilidade real em USD.

### Series para visualizacao

- `public/assets/presentation.js`
- `public/assets/app.js`

Responsabilidades:

- gerar no navegador as curvas comparativas do grafico;
- considerar apenas dias uteis presentes nas series oficiais;
- manter a mesma logica economica do calculo analitico;
- formatar derivados de apresentacao para BRL, USD/BRL e posicao em USD.

### Validacao cruzada

- `scripts/validate_static_reference_cases.py`
- `scripts/js_calculate_static.mjs`
- `tests/fixtures/static_reference_periods.json`

Responsabilidades:

- comparar resultados JavaScript contra o nucleo Python em periodos reais de referencia;
- impedir divergencias silenciosas entre a pagina publicada e a fonte de verdade em Python.

### Modelos e erros

- `armadilha_cdi/models.py`
- `armadilha_cdi/exceptions.py`

Responsabilidades:

- tipar a troca de dados entre camadas;
- centralizar objetos de retorno e excecoes de dominio.

## Fluxo de execucao

1. O workflow ou operador roda `scripts/export_static_market_data.py`.
2. O exportador usa `BCBMarketDataProvider` para obter CDI e USD/BRL, reaproveitando o cache JSON local quando possivel.
3. O exportador valida schema, cobertura e sinais de segredo, escreve `public/data/market-data.latest.json` e gera o manifesto.
4. `scripts/validate_static_reference_cases.py` compara o calculo JavaScript contra `armadilha_cdi/services/calculations.py`.
5. O Cloudflare Pages serve `public/`.
6. O navegador do usuario carrega o dataset estatico, calcula localmente e renderiza a analise.

## Regras centrais preservadas na arquitetura

- CDI acumulado com `data_inicial_efetiva <= data < data_final_efetiva`;
- data inicial em 01/07/1994 ou depois, sem fallback para dados anteriores ao real;
- datas sem dado oficial resolvidas para o ultimo dia util disponivel, exceto a borda inicial sem CDI anterior permitido, que pode usar o primeiro CDI oficial dentro da tolerancia;
- cotacao USD/BRL com fallback de ate 15 dias para tras;
- metrica principal: variacao % em USD;
- notificacao explicita quando a cotacao usada nao coincide com a data solicitada;
- dataset estatico versionado, sem segredos e com cobertura visivel na interface.

## Por que essa separacao importa

- facilita testes unitarios sem depender de interface web Python;
- reduz o risco de misturar apresentacao com regra financeira;
- permite adicionar uma API HTTP no futuro sem reescrever o nucleo do calculo;
- mantem o projeto orientado a uma publicacao simples, barata e estavel;
- preserva a pagina publica mesmo quando a atualizacao diaria de dados falha.

## Direcao futura

Esta estrutura foi pensada para suportar evolucoes sem quebrar o MVP:

- entrada de novas series, como IPCA;
- eventual comparacao com inflacao americana;
- exposicao por API;
- cache em storage de objetos ou outro servico gerenciado, se o cache JSON local do workflow deixar de ser suficiente.
