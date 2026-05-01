# Arquitetura

## Visao geral

O projeto foi organizado para manter a regra financeira desacoplada da interface. A ideia central e simples: a camada de apresentacao pode mudar, mas a logica que responde se houve ganho ou perda relativa em dolar precisa continuar previsivel e testavel.

A base ativa nao depende mais de scripts exploratorios. A memoria tecnica da fase inicial foi consolidada em `README.md`, `AGENTS.md` e nos documentos desta pasta.

## Camadas do projeto

### Interface

- `app.py`
- `armadilha_cdi/frontpage_texts.py`

Responsabilidades:

- receber `data inicial`, `data final` e `valor inicial`;
- centralizar os textos exibidos na frontpage;
- chamar o provider de dados;
- acionar a regra de calculo;
- renderizar cards, tabela-resumo e grafico;
- exibir mensagens de erro e observacoes de fallback.

### Integracao com dados de mercado

- `armadilha_cdi/services/data_providers.py`

Responsabilidades:

- consultar CDI no Banco Central;
- consultar PTAX USD/BRL no Banco Central;
- sincronizar dados com o cache configurado;
- buscar apenas as bordas ausentes quando o cache ja cobre parte da janela;
- tratar bordas de CDI sem observacoes oficiais como janelas vazias quando o SGS nao retorna dados;
- devolver um `MarketDataBundle` pronto para a camada de calculo.

### Cache

- `armadilha_cdi/services/cache.py`

Responsabilidades:

- definir o contrato comum de persistencia de series;
- persistir series em arquivos JSON;
- persistir series em Postgres/Supabase para publicacao;
- carregar historico ja existente;
- fazer merge incremental com novos dados;
- proteger load/merge/save com lock por arquivo;
- gravar por substituicao atomica para evitar JSON parcial;
- gravar em Postgres com `UPSERT` por serie e data;
- evitar recaptura completa do historico a cada execucao.

O cache local e adequado para desenvolvimento e execucao local. Para publicacao, o backend preferencial e Supabase/Postgres, configurado por ambiente com `MARKET_DATA_CACHE_BACKEND=supabase` e `SUPABASE_DATABASE_URL`.

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
- impedir periodos iniciados antes da entrada em circulacao do real brasileiro, em 01/07/1994;
- resolver datas solicitadas para dias uteis oficiais;
- resolver a borda inicial do real para o primeiro CDI oficial disponivel quando nao ha CDI anterior permitido;
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
3. O provider consulta o cache configurado e completa apenas as bordas ausentes da janela no Banco Central quando necessario. Para CDI, janelas longas sao fatiadas em requisicoes menores ao SGS/BCB, com breve pausa entre chamadas.
4. A camada de calculo resolve o periodo efetivo de mercado, acumula o CDI e resolve as cotacoes USD/BRL com fallback.
5. A camada de grafico prepara a serie comparativa em dias uteis oficiais.
6. A interface apresenta o resumo analitico e o grafico.

Em operacao publicada, o fluxo preferencial e rodar `scripts/sync_market_data.py` de forma manual ou agendada antes do uso. Assim, o caminho interativo tende a ler dados ja sincronizados e so usa a sincronizacao sob demanda como fallback.

Na publicacao com Supabase, a tabela padrao e `market_rates`, com chave primaria `(series, ref_date)`. O app cria essa tabela automaticamente ao iniciar o backend Postgres, mas a mesma definicao tambem pode ser criada manualmente em migracao SQL:

```sql
create table if not exists market_rates (
  series text not null,
  ref_date date not null,
  value numeric not null,
  updated_at timestamptz not null default now(),
  primary key (series, ref_date)
);
```

## Regras centrais preservadas na arquitetura

- CDI acumulado com `data_inicial_efetiva <= data < data_final_efetiva`
- data inicial em 01/07/1994 ou depois, sem fallback para dados anteriores ao real
- datas sem dado oficial resolvidas para o ultimo dia util disponivel, exceto a borda inicial sem CDI anterior permitido, que pode usar o primeiro CDI oficial dentro da tolerancia
- cotacao USD/BRL com fallback de ate 15 dias para tras
- metrica principal: variacao % em USD
- notificacao explicita quando a cotacao usada nao coincide com a data solicitada

## Por que essa separacao importa

- facilita testes unitarios sem depender do Streamlit;
- reduz o risco de misturar interface com regra financeira;
- permite adicionar uma API HTTP no futuro sem reescrever o nucleo do calculo;
- permite alternar entre cache local e Supabase sem mexer na UI ou na regra financeira;
- mantem o projeto orientado a uma estrutura de producao simples, em vez de depender de material exploratorio.

## Direcao futura

Esta estrutura foi pensada para suportar evolucoes sem quebrar o MVP:

- entrada de novas series, como IPCA;
- eventual comparacao com inflacao americana;
- exposicao por API;
- rotina agendada de sincronizacao diaria do backend Supabase;
- camada adicional de cache de leitura em memoria sobre o backend persistente, se houver necessidade.
