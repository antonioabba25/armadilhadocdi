# Armadilha do CDI

## Objetivo do projeto

Este projeto nasce de uma exploração em notebook e está evoluindo para uma aplicação web simples.

O escopo atual da aplicação é:

- receber `data inicial`
- receber `data final`
- receber `valor inicial investido` em BRL
- retornar um resultado analítico
- retornar um gráfico comparativo

O objetivo do produto não é apenas mostrar o rendimento nominal do CDI em reais.

O foco real é responder se um valor aplicado em CDI entre duas datas preservou, perdeu ou ganhou poder relativo quando observado em dólar. Em outras palavras: a aplicação compara o crescimento nominal em BRL com a variação cambial do USD/BRL para revelar a possível "armadilha" de achar que o ganho em CDI foi suficiente.

## Arquivos de inspiração

Os dois arquivos de referência conceitual para este projeto são:

- `exploracaonotebook/calc_armadilhacdi.py`
- `calculo_inflacaoamericana.py`

### Papel de `exploracaonotebook/calc_armadilhacdi.py`

Esse é o arquivo principal de inspiração da regra de negócio atual.

Ele mistura:

- coleta de dados do Banco Central
- rotinas de cache
- fallback para datas sem cotação
- cálculo analítico do investimento
- geração de gráfico comparativo

Ele não está estruturado como código de produção, mas define bem a essência funcional do projeto web.

### Papel de `calculo_inflacaoamericana.py`

Esse arquivo não representa o fluxo principal da aplicação atual, mas ajuda a esclarecer a intenção econômica mais ampla do projeto: raciocinar sobre preservação de poder de compra em moeda forte, especialmente em dólar.

Ele serve como inspiração complementar porque:

- reforça a leitura do problema como comparação de poder de compra, e não apenas de rentabilidade nominal
- mostra uma abordagem de tratamento de séries históricas com datas de cobertura imperfeita
- sugere uma possível linha futura de expansão analítica com inflação americana ou métricas reais em USD

Para a versão atual da aplicação web, o núcleo obrigatório continua sendo `CDI + USD/BRL`. A lógica de inflação americana deve ser tratada como referência conceitual ou extensão futura, e não como dependência mínima do MVP.

## Lógica de negócio identificada

### 1. Fontes de dados

O fluxo principal do notebook usa dados públicos do Banco Central do Brasil:

- `CDI` pela série `12`
- `USD/BRL` por PTAX via API Olinda e, em alguns trechos, também pela série `1`
- `IPCA` pela série `433` para compor o gráfico histórico

Fontes e abordagens usadas no notebook:

- API `bcdata.sgs.12` em JSON para CDI
- fallback SOAP do BCB para CDI
- API Olinda PTAX para dólar venda
- `python-bcb` com `sgs.get(...)` para consultas em bloco

O arquivo `calculo_inflacaoamericana.py` usa dados do FRED para CPI dos EUA. Essa fonte não faz parte do contrato mínimo atual da aplicação, mas registra uma direção possível para análises futuras de poder de compra em dólar.

## Regras funcionais principais

### 2. Sincronização e cache

O notebook tenta evitar dependência total de chamadas online a cada execução:

- guarda cache local de CDI
- guarda cache local de USD
- atualiza quando o cache está vazio ou atrasado

Isso é importante para a versão web, mas a implementação final deve decidir entre:

- cache em arquivo local
- cache em banco
- atualização on-demand com memoização

### 3. Fallback de datas sem cotação

Nem toda data tem cotação disponível, especialmente fins de semana e feriados.

O notebook resolve isso buscando o último valor disponível ao retroceder até 15 dias. Essa regra aparece para USD e é importante manter algo equivalente na aplicação web.

Regra prática:

- se não houver cotação exatamente na data pedida
- procurar a cotação anterior mais próxima
- limitar a retroação para evitar resultados silenciosamente errados

### 4. Acúmulo do CDI

O coração do cálculo é a capitalização diária das taxas de CDI:

`fator_acumulado *= (1 + taxa_diaria / 100)`

Depois:

- `valor_final_brl = valor_inicial_brl * fator_acumulado`
- `cdi_percentual = (fator_acumulado - 1) * 100`

### 5. Conversão para dólar

O notebook compara o capital investido com a taxa de câmbio do início e do fim:

- `usd_inicial = valor_inicial_brl / cotacao_inicial`
- `usd_final_com_cdi = valor_final_brl / cotacao_final`

Com isso ele calcula o ganho real em dólar:

`rentabilidade_usd_real = (usd_final_com_cdi / usd_inicial - 1) * 100`

Essa é a métrica mais importante do projeto.

Na prática, essa métrica representa a evolução do poder de compra em dólares de um capital que ficou aplicado em CDI em reais ao longo do período selecionado.

## Saída analítica esperada

A aplicação web deve, no mínimo, devolver:

- período consultado
- valor inicial em BRL
- valor final corrigido pelo CDI em BRL
- CDI acumulado no período
- cotação USD/BRL inicial usada
- cotação USD/BRL final usada
- equivalente em USD no início
- equivalente em USD no fim após correção pelo CDI
- ganho real em USD

## Saída gráfica esperada

O notebook também aponta para um gráfico histórico comparativo. As séries calculadas ali são:

- evolução acumulada do `CDI`
- evolução acumulada do `IPCA`
- variação acumulada do `USD`
- ganho real em `USD` do capital corrigido por CDI

Para o frontend, o gráfico pode começar simples, com foco em:

- `CDI acumulado (%)`
- `USD acumulado (%)`
- `ganho real em USD (%)`

O `IPCA` pode entrar como série opcional depois.

Uma extensão futura possível, inspirada por `calculo_inflacaoamericana.py`, é incluir uma camada adicional de comparação com inflação americana ou outra métrica de poder de compra em USD, mas isso não deve complicar o MVP inicial.

## Inconsistências atuais do notebook

O arquivo de exploração tem blocos duplicados e regras ligeiramente diferentes entre si. Isso é esperado em material exploratório, mas a versão web deve consolidar uma única regra.

### 1. Janela do CDI

Há pelo menos duas variações no notebook:

- `d_ini < data <= d_fim`
- `d_ini <= data < d_fim`

Além disso, em uma versão com `sgs.get(...)`, o código usa `df['cdi'][:-1]`, o que equivale a incluir o começo e excluir o último dia.

### 2. Regra recomendada para a aplicação web

A regra mais consistente no notebook parece ser:

- incluir a taxa a partir da `data inicial`
- excluir a `data final` do acúmulo do CDI

Isto é, usar:

`data_inicial <= data < data_final`

Motivo:

- essa regra aparece explicitamente no bloco marcado como "Regra exata validada"
- ela também é compatível com o uso de `df['cdi'][:-1]`

Se essa convenção for alterada depois, isso deve ser tratado como decisão de produto e não como detalhe técnico.

## Arquitetura sugerida para a aplicação web

Mesmo que a interface seja simples, a lógica já pede separação clara de responsabilidades:

- `camada de coleta de dados`
- `camada de cache`
- `camada de cálculo`
- `camada de serialização para API`
- `camada de frontend para formulário + gráfico`

Estrutura conceitual sugerida:

- `services/data_providers`: buscar CDI, USD e eventualmente IPCA
- `services/cache`: leitura e escrita de cache
- `services/calculations`: regra financeira principal
- `services/charts`: preparação das séries para visualização
- `api`: endpoint que recebe datas e valor
- `frontend`: formulário e componentes de resultado

## Contrato mínimo de cálculo

Uma função central da aplicação pode seguir esta ideia:

```python
def calcular_resultado(data_inicial: str, data_final: str, valor_inicial_brl: float) -> dict:
    ...
```

Resposta esperada:

```python
{
    "periodo": "01/01/2020 a 01/01/2024",
    "brl_ini": 10000.0,
    "brl_fim": 14500.0,
    "cdi_perc": 45.0,
    "cotacao_ini": 4.02,
    "cotacao_fim": 5.31,
    "usd_ini": 2487.56,
    "usd_fim_com_cdi": 2730.70,
    "rentabilidade_usd_real": 9.77
}
```

## Cuidados importantes

- validar formato de data com clareza
- impedir `data final` menor ou igual à `data inicial`
- tratar ausência de dados de mercado de forma explícita
- documentar qual cotação foi usada quando houver fallback
- evitar recalcular todo o histórico a cada requisição
- separar código exploratório de código de produção

## Leitura correta do projeto

Este projeto não é apenas uma "calculadora de rendimento CDI".

Ele é uma aplicação comparativa para responder:

"Se eu deixei meu dinheiro rendendo CDI entre duas datas, minha posição relativa em dólar melhorou, piorou ou apenas pareceu ter melhorado em reais?"

Essa pergunta deve orientar tanto o backend quanto a experiência do usuário.

Em termos de produto, a leitura mais fiel é:

- entrada simples, com `data inicial`, `data final` e `valor inicial`
- saída analítica objetiva, com foco em BRL final, USD inicial, USD final e ganho real em USD
- gráfico comparativo que ajude a visualizar a diferença entre rendimento nominal e preservação de poder relativo em dólar

## Próximo passo recomendado

Ao transformar os scripts exploratórios em aplicação web, a prioridade deve ser:

1. consolidar uma única regra de cálculo
2. extrair a lógica financeira para um módulo limpo e testável
3. expor um endpoint simples para consulta
4. montar uma UI com formulário, cards de resumo e gráfico comparativo

## Resumo executivo

Os arquivos exploratórios mostram que a lógica central do projeto já está validada em nível conceitual:

- buscar CDI e USD do BCB
- acumular CDI diariamente
- converter o capital inicial e final para USD
- medir a rentabilidade real em dólar
- exibir comparação analítica e gráfica

E, de forma complementar:

- usar a ideia de inflação americana apenas como inspiração para leituras futuras de poder de compra em USD

A aplicação web deve preservar essa essência, removendo duplicações, consolidando a regra temporal do cálculo e organizando o código em camadas mais previsíveis.
