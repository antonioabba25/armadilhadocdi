# Arquitetura

## Visao geral

O projeto foi organizado para manter a regra financeira desacoplada da interface. A ideia central e simples: a camada de apresentacao pode mudar, mas a logica que responde se houve ganho ou perda relativa em dolar precisa continuar previsivel e testavel.

A base ativa nao depende mais de scripts exploratorios. A memoria tecnica da fase inicial foi consolidada em `README.md`, `AGENTS.md` e nos documentos desta pasta.

## Camadas do projeto

### Interface

- `app.py`

Responsabilidades:

- receber `data inicial`, `data final` e `valor inicial`;
- chamar o provider de dados;
- acionar a regra de calculo;
- renderizar cards, tabela-resumo e grafico;
- exibir mensagens de erro e observacoes de fallback.

### Integracao com dados de mercado

- `armadilha_cdi/services/data_providers.py`

Responsabilidades:

- consultar CDI no Banco Central;
- consultar PTAX USD/BRL no Banco Central;
- sincronizar dados com o cache local;
- devolver um `MarketDataBundle` pronto para a camada de calculo.

### Cache

- `armadilha_cdi/services/cache.py`

Responsabilidades:

- persistir series em arquivos JSON;
- carregar historico ja existente;
- fazer merge incremental com novos dados;
- proteger load/merge/save com lock por arquivo;
- gravar por substituicao atomica para evitar JSON parcial;
- evitar recaptura completa do historico a cada execucao.

O cache local e adequado para o MVP e para uma publicacao simples em processo unico. Ele nao deve ser tratado como banco definitivo em producao com multiplas instancias; nesse caso, a camada deve evoluir para banco, storage compartilhado ou outro mecanismo transacional.

### Sincronizacao operacional

- `scripts/sync_market_data.py`

Responsabilidades:

- preaquecer ou atualizar o cache fora da requisicao do usuario;
- permitir agendamento externo, por exemplo cron ou job da plataforma;
- reduzir consultas ao Banco Central durante o uso interativo do Streamlit.

### Regra de negocio

- `armadilha_cdi/services/calculations.py`

Responsabilidades:

- validar entradas de dominio;
- resolver datas solicitadas para dias uteis oficiais;
- aplicar a janela oficial do CDI sobre o periodo efetivo;
- resolver cotacoes com fallback;
- calcular BRL final, USD inicial, USD final e rentabilidade real em USD.

### Series para visualizacao

- `armadilha_cdi/services/charts.py`

Responsabilidades:

- transformar series historicas em um `DataFrame`;
- preparar as curvas comparativas mostradas no Streamlit;
- considerar apenas dias uteis presentes nas series oficiais;
- manter a mesma logica economica do calculo analitico.

### Modelos e erros

- `armadilha_cdi/models.py`
- `armadilha_cdi/exceptions.py`

Responsabilidades:

- tipar a troca de dados entre camadas;
- centralizar objetos de retorno e excecoes de dominio.

## Fluxo de execucao

1. O usuario informa data inicial, data final e valor inicial em BRL.
2. A interface pede ao provider os dados de mercado necessarios para a janela selecionada.
3. O provider consulta cache local e completa a janela no Banco Central quando necessario.
4. A camada de calculo resolve o periodo efetivo de mercado, acumula o CDI e resolve as cotacoes USD/BRL com fallback.
5. A camada de grafico prepara a serie comparativa em dias uteis oficiais.
6. A interface apresenta o resumo analitico e o grafico.

Em operacao publicada, o fluxo preferencial e rodar `scripts/sync_market_data.py` de forma manual ou agendada antes do uso. Assim, o caminho interativo tende a ler dados ja sincronizados e so usa a sincronizacao sob demanda como fallback.

## Regras centrais preservadas na arquitetura

- CDI acumulado com `data_inicial_efetiva <= data < data_final_efetiva`
- datas sem dado oficial resolvidas para o ultimo dia util disponivel
- cotacao USD/BRL com fallback de ate 15 dias para tras
- metrica principal: ganho real em USD
- notificacao explicita quando a cotacao usada nao coincide com a data solicitada

## Por que essa separacao importa

- facilita testes unitarios sem depender do Streamlit;
- reduz o risco de misturar interface com regra financeira;
- permite adicionar uma API HTTP no futuro sem reescrever o nucleo do calculo;
- permite trocar o cache local por banco sem mexer na UI ou na regra financeira;
- mantem o projeto orientado a uma estrutura de producao simples, em vez de depender de material exploratorio.

## Direcao futura

Esta estrutura foi pensada para suportar evolucoes sem quebrar o MVP:

- entrada de novas series, como IPCA;
- eventual comparacao com inflacao americana;
- exposicao por API;
- troca do mecanismo de cache local por banco ou camada de memoizacao mais robusta.
