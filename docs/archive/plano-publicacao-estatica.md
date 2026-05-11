# Plano de Implementacao: Publicacao Estatica em Cloudflare Pages

Este plano descreve a migracao planejada para uma versao web estatica da aplicacao, usando Cloudflare Pages, calculo no navegador e dados CDI/USD pre-gerados diariamente.

O objetivo nao e substituir imediatamente o MVP Streamlit. O objetivo e criar uma nova superficie publica, mais barata e mais estavel, preservando a leitura correta do produto:

> Se um capital ficou aplicado em CDI entre duas datas, a posicao relativa em dolar melhorou, piorou ou apenas pareceu ter melhorado em reais?

## Status da Implementacao Local

As etapas 1 a 11 possuem implementacao local inicial:

- contrato de calculo: `docs/contrato-calculo-estatico.md`;
- schema do dataset: `docs/dataset-estatico.md`;
- exportador: `scripts/export_static_market_data.py`;
- calculo JS e series do grafico: `public/assets/calculations.js`;
- UI estatica: `public/index.html`, `public/assets/app.js`, `public/assets/styles.css`;
- atualizacao diaria: `.github/workflows/update-static-market-data.yml`;
- validacao cruzada: `tests/fixtures/static_reference_periods.json` e `scripts/validate_static_reference_cases.py`;
- publicacao/manutencao: `docs/publicacao.md`.

O deploy em Cloudflare Pages e a troca de URL principal ainda dependem de validacao em ambiente real.

## Principios da Solucao

- O servidor nao deve calcular resultados por usuario.
- O navegador deve executar o calculo a partir de dados oficiais ja publicados em arquivos estaticos.
- O Banco Central nao deve ser consultado durante a interacao do usuario.
- Os dados CDI e USD/BRL devem ser atualizados por rotina agendada.
- A regra financeira deve continuar equivalente ao MVP Python.
- A migracao deve ser feita em etapas pequenas, cada uma testavel isoladamente.
- O Streamlit deve continuar funcionando ate a nova publicacao estar validada.

## Arquitetura Alvo

```text
Cloudflare Pages
  index.html
  assets/
    app.js
    styles.css
  data/
    market-data.latest.json
    market-data.manifest.json

GitHub Actions ou rotina equivalente
  scripts/export_static_market_data.py
    consulta/sincroniza cache
    gera JSON estatico
    valida schema
    publica via commit/deploy

Navegador
  carrega JSON estatico
  valida entradas
  resolve datas efetivas
  acumula CDI
  calcula comparacao BRL vs USD
  renderiza resumo e grafico
```

## Etapa 1: Congelar Contrato de Calculo

Objetivo: definir exatamente o comportamento que a versao web deve reproduzir.

Entregaveis:

- Documento curto com os casos de negocio obrigatorios.
- Lista de campos de entrada e saida equivalentes a `CalculationResult`.
- Conjunto minimo de cenarios de referencia extraidos dos testes Python atuais.

Validacao:

- Rodar os testes atuais:

```bash
python3 -m unittest discover -s tests -v
```

- Escolher datas representativas:
  - periodo curto em dias uteis;
  - periodo com fim de semana/feriado;
  - periodo com data inicial sem CDI anterior permitido;
  - periodo com fallback de PTAX;
  - periodo invalido ou sem dados suficientes.

Criterio de avanco:

- Todos os casos esperados estao documentados.
- A regra da janela `data_inicial_efetiva <= data < data_final_efetiva` esta explicita.
- A metrica central continua sendo `real_usd_return_percentage`.

## Etapa 2: Definir Schema do Dataset Estatico

Objetivo: criar um formato estavel para transportar dados oficiais ao navegador.

Entregaveis:

- Schema do arquivo `data/market-data.latest.json`.
- Schema do arquivo `data/market-data.manifest.json`.
- Decisao sobre granularidade: arquivo unico inicial ou arquivos particionados por ano.

Formato inicial sugerido:

```json
{
  "schema_version": 1,
  "generated_at": "2026-05-11T00:00:00Z",
  "source": {
    "cdi": "BCB SGS serie 12",
    "usdbrl": "BCB Olinda PTAX venda"
  },
  "coverage": {
    "start_date": "1994-07-01",
    "end_date": "2026-05-08"
  },
  "cdi_rates": {
    "2026-05-08": 0.042239
  },
  "usd_rates": {
    "2026-05-08": 5.6789
  }
}
```

Validacao:

- Conferir que todas as datas estao em `YYYY-MM-DD`.
- Conferir que taxas e cotacoes sao numeros.
- Conferir que o dataset possui cobertura suficiente para os casos da Etapa 1.
- Conferir tamanho final do JSON gerado.

Criterio de avanco:

- O schema suporta as regras atuais sem inferencias ambiguas.
- O arquivo pode ser versionado ou publicado como artefato estatico sem segredo.
- O tamanho e aceitavel para carregamento inicial em pagina web.

## Etapa 3: Criar Exportador de Dados Estaticos

Objetivo: gerar o dataset estatico a partir do mesmo pipeline de dados do MVP.

Entregaveis:

- Script `scripts/export_static_market_data.py`.
- Saida em `public/data/` ou diretorio equivalente definido na implementacao.
- Validacao de schema no proprio script.

Comportamento esperado:

- Reusar os provedores e cache existentes.
- Sincronizar apenas bordas ausentes quando possivel.
- Gerar JSON de forma deterministica.
- Falhar com mensagem clara quando houver ausencia real de dados.
- Nao depender do Streamlit.

Validacao:

```bash
python3 scripts/export_static_market_data.py --start 1994-07-01
python3 -m unittest discover -s tests -v
```

Checks manuais:

- Abrir o JSON e conferir `schema_version`, `generated_at`, `coverage`, `cdi_rates` e `usd_rates`.
- Confirmar que `cache/` continua nao versionado.
- Confirmar que o arquivo publicado nao contem credenciais.

Criterio de avanco:

- O exportador gera dados completos localmente.
- O arquivo gerado reproduz os dados oficiais esperados.
- O script pode ser executado em ambiente de CI.

## Etapa 4: Portar o Calculo Para JavaScript Puro

Objetivo: implementar no navegador a mesma regra financeira do Python.

Entregaveis:

- Modulo JavaScript de calculo, por exemplo `public/assets/calculations.js`.
- Funcoes puras para:
  - validar entradas;
  - resolver datas efetivas de CDI;
  - resolver fallback de USD/BRL;
  - acumular CDI;
  - calcular resultado final.
- Testes automatizados em JavaScript.

Validacao:

- Executar testes JS contra os mesmos cenarios da Etapa 1.
- Comparar saidas JS vs Python para:
  - `final_brl`;
  - `cdi_percentage`;
  - `effective_start_date`;
  - `effective_end_date`;
  - `initial_fx_date`;
  - `final_fx_date`;
  - `real_usd_return_percentage`;
  - `cdi_days_used`.

Criterio de avanco:

- Diferencas numericas estao dentro de tolerancia definida.
- As mensagens de erro essenciais continuam claras.
- Nenhuma regra financeira foi alterada para facilitar a UI.

## Etapa 5: Criar Interface Web Estatica Minima

Objetivo: entregar a primeira pagina utilizavel sem backend.

Entregaveis:

- `index.html`.
- CSS proprio e leve.
- JavaScript de interface.
- Formulario com:
  - data inicial;
  - data final;
  - valor inicial em BRL.
- Resumo com as mesmas metricas centrais do MVP.

Validacao:

- Abrir localmente a pagina estatica.
- Testar entradas validas e invalidas.
- Confirmar que a pagina carrega o dataset estatico.
- Confirmar que a UI informa quando a data efetiva da cotacao difere da data solicitada.

Criterio de avanco:

- Usuario consegue executar a analise completa sem servidor Python.
- O resultado principal compara crescimento nominal em BRL com posicao relativa em USD.
- A experiencia minima funciona em desktop e celular.

## Etapa 6: Implementar Grafico no Navegador

Objetivo: reproduzir a comparacao visual do MVP usando apenas dados estaticos.

Entregaveis:

- Serie derivada para evolucao nominal em BRL.
- Serie derivada para posicao relativa em USD.
- Grafico responsivo.

Validacao:

- Comparar a serie gerada no navegador com a serie Python de `charts.py` para casos de referencia.
- Confirmar que apenas dias uteis presentes nas series oficiais entram no grafico.
- Verificar legibilidade em tela pequena.

Criterio de avanco:

- O grafico sustenta a tese do produto sem distorcer a regra financeira.
- Periodos sem dados oficiais nao aparecem como pontos artificiais.
- A visualizacao nao exige chamadas dinamicas ao servidor.

## Etapa 7: Automatizar Atualizacao Diaria dos Dados

Objetivo: atualizar CDI/USD sem acao manual e sem custo por usuario.

Entregaveis:

- Workflow agendado, preferencialmente GitHub Actions.
- Execucao diaria em horario posterior a publicacao esperada dos dados oficiais.
- Commit automatico ou artefato publicado no branch de deploy.

Validacao:

- Rodar o workflow manualmente.
- Conferir diff contendo apenas dados esperados.
- Conferir logs de falha quando dados do dia ainda nao existem.
- Confirmar que uma falha de atualizacao nao derruba a pagina ja publicada.

Criterio de avanco:

- Atualizacao diaria funciona sem segredos sensiveis quando usando cache local.
- Se Supabase/Postgres for usado, credenciais ficam somente em secrets do CI.
- A pagina sempre consegue usar o ultimo dataset valido.

## Etapa 8: Preparar Deploy no Cloudflare Pages

Objetivo: publicar a versao estatica em ambiente real.

Entregaveis:

- Diretorio de publicacao definido, por exemplo `public/`.
- Configuracao de build no Cloudflare Pages.
- Variaveis de ambiente documentadas, se houver.
- URL de preview.

Configuracao inicial sugerida:

- Framework preset: nenhum ou static site.
- Build command: comando que roda testes e exporta dados, se adequado.
- Output directory: `public`.

Validacao:

- Fazer deploy de preview.
- Testar a URL publica em navegador anonimo.
- Confirmar que os arquivos em `data/` sao servidos corretamente.
- Confirmar headers/cache basicos.

Criterio de avanco:

- A aplicacao funciona fora da maquina local.
- Nao ha dependencia de processo Python ativo.
- O primeiro carregamento e aceitavel em rede comum.

## Etapa 9: Validacao Cruzada Com o MVP Streamlit

Objetivo: garantir que a nova versao publica nao mudou o produto.

Entregaveis:

- Planilha ou arquivo de fixtures com casos comparativos.
- Resultado lado a lado: Streamlit/Python vs Web/JS.
- Registro de diferencas e decisoes.

Validacao:

- Executar ao menos 10 periodos reais.
- Incluir periodos longos, curtos, com feriados e com fallback de PTAX.
- Conferir arredondamentos apresentados ao usuario.

Criterio de avanco:

- Resultados equivalentes nos campos essenciais.
- Diferencas, se existirem, sao apenas de arredondamento visual.
- Documentacao de metodologia continua verdadeira.

## Etapa 10: Troca Gradual da Publicacao

Objetivo: colocar a versao estatica como publicacao principal sem perder o fallback Streamlit.

Entregaveis:

- Link publico da Cloudflare Pages.
- README atualizado com a nova forma de publicacao.
- `docs/arquitetura.md` atualizado.
- `docs/publicacao.md` atualizado.

Validacao:

- Acessar a pagina em desktop e celular.
- Testar um periodo recente e um periodo historico.
- Conferir que o Streamlit ainda roda localmente:

```bash
streamlit run app.py
```

Criterio de avanco:

- Cloudflare Pages passa a ser a URL recomendada.
- Streamlit permanece como ferramenta local/admin, se ainda fizer sentido.
- O fluxo de atualizacao diaria esta documentado.

## Etapa 11: Observabilidade Simples e Manutencao

Objetivo: manter a publicacao barata, previsivel e facil de diagnosticar.

Entregaveis:

- Indicador visivel ou discreto de data da ultima atualizacao dos dados.
- Log do workflow de atualizacao.
- Checklist de recuperacao em caso de falha de dados.

Validacao:

- Simular ausencia de dados oficiais recentes.
- Confirmar que a pagina informa a cobertura disponivel.
- Confirmar que o usuario nao recebe resultado com dados fora da tolerancia.

Criterio de avanco:

- Falhas de atualizacao sao detectaveis.
- A pagina continua funcionando com o ultimo dataset valido.
- Nao ha custo recorrente por acesso normal de usuario.

## Riscos e Decisoes Pendentes

- Tamanho do dataset desde 1994: validar se arquivo unico e suficiente ou se sera melhor particionar por ano.
- Fonte de atualizacao diaria: decidir entre cache JSON local no CI ou Supabase/Postgres como fonte operacional.
- Biblioteca de grafico: escolher opcao leve, ou implementar com SVG/canvas simples.
- Estrategia de arredondamento: manter equivalencia visual com o Streamlit.
- Frequencia de atualizacao: diaria em dias uteis pode ser suficiente; execucoes extras podem cobrir atrasos de publicacao do BCB.

## Definicao de Pronto da Solucao

A solucao sera considerada pronta quando:

- A pagina estatica no Cloudflare Pages calcular os mesmos resultados do MVP.
- O dataset CDI/USD for atualizado automaticamente.
- O usuario nao depender de um servidor Streamlit acordado.
- A comparacao BRL nominal vs poder relativo em USD continuar sendo o resultado principal.
- Os testes Python e JavaScript cobrirem os cenarios financeiros essenciais.
- A documentacao explicar claramente a nova arquitetura e o fluxo de publicacao.
