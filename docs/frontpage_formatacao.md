# Regras e parâmetros de formatação da frontpage

Este documento descreve a frontpage atual do projeto **Armadilha do CDI** e os limites que devem ser preservados em uma otimização visual feita em serviço externo, como o Stitch.

## Objetivo da tela

A frontpage não é uma calculadora genérica de rendimento em CDI. A tela deve responder, de forma imediata:

> Se um capital ficou aplicado em CDI entre duas datas, a posição relativa em dólar melhorou, piorou ou apenas pareceu ter melhorado em reais?

A hierarquia visual deve favorecer a comparação entre:

- crescimento nominal em BRL pelo CDI;
- variação acumulada do USD/BRL;
- resultado relativo em USD, medido principalmente por `real_usd_return_percentage`.

## Plataforma atual

- Aplicação em Streamlit.
- Layout configurado como `wide`.
- Frontpage renderizada em `app.py`.
- Textos centralizados em `armadilha_cdi/frontpage_texts.py`.
- Gráfico gerado com `st.line_chart`.
- Tabelas geradas com `st.dataframe`.
- Não há CSS customizado ativo no MVP atual.

## Estrutura da página

A ordem atual dos blocos da frontpage é:

1. Título principal.
2. Descrição curta do produto.
3. Legenda de intervalo mínimo de datas.
4. Formulário de entrada em uma linha com três colunas.
5. Estado vazio ou loading.
6. Métricas principais.
7. Notas de cotação e período efetivo.
8. Tabela técnica.
9. Gráfico comparativo.
10. Expander com base diária do gráfico.
11. Expander com metodologia.

Essa ordem pode ser refinada visualmente, mas a tela deve continuar conduzindo o usuário de entrada -> métricas -> evidências.

## Conteúdo textual fixo

### Cabeçalho

- Título da página: `Armadilha do CDI`
- Descrição: `Compare o crescimento nominal de aplicacao no CDI em reais com a variacao do dolar para entender se o CDI realmente valorizou em termos de variacao do USD.`
- Legenda de datas: `Informe datas a partir de {earliest_date}.`

Observação para redesign: pode-se corrigir acentos na interface final se os arquivos de copy forem atualizados junto com a implementação. O sentido do texto não deve mudar sem decisão explícita.

### Formulário

- Label 1: `Data inicial`
- Label 2: `Data final`
- Label 3: `Valor inicial investido (BRL)`
- Botão de envio: `Analisar periodo`

### Estados

- Estado vazio: `Preencha o formulario e clique em 'Analisar periodo' para gerar o resultado.`
- Loading: `Buscando dados do Banco Central e calculando o resultado...`
- Erro inesperado: `Ocorreu um erro inesperado: {error}`

### Seções de resultado

- Gráfico: `Grafico comparativo`
- Expander do gráfico: `Ver base diaria do grafico`
- Expander metodológico: `Metodologia usada`

## Parâmetros dos inputs

### Data inicial

- Tipo: date input.
- Valor padrão: data atual menos 365 dias.
- Data mínima: `EARLIEST_SUPPORTED_DATE`, hoje equivalente a 01/07/1994.
- Data máxima: data atual.
- Formato exibido: `DD/MM/YYYY`.

### Data final

- Tipo: date input.
- Valor padrão: data atual.
- Data mínima: `EARLIEST_SUPPORTED_DATE`, hoje equivalente a 01/07/1994.
- Data máxima: data atual.
- Formato exibido: `DD/MM/YYYY`.

### Valor inicial investido

- Tipo: number input.
- Valor mínimo: `0.01`.
- Valor padrão: `10000.00`.
- Incremento: `100.00`.
- Formato: duas casas decimais.

## Layout do formulário

- O formulário usa três colunas de mesma largura.
- Em desktop, os três campos devem ficar na mesma linha.
- Em mobile, os campos podem empilhar verticalmente.
- O botão de envio pertence ao formulário e deve aparecer após os campos.
- O botão deve ser visualmente claro como ação primária da tela.

## Resumo analítico

O resumo não exibe mais um alerta de conclusão dizendo se o CDI compensou ou não a variação do dólar. A leitura deve ser feita pelas métricas principais, especialmente o resultado relativo em USD, pela tabela técnica e pelo gráfico comparativo.

## Métricas

As métricas são apresentadas em dois grupos.

### Primeira linha

Usa três colunas:

- `Valor inicial`
- `Valor final com CDI em BRL`
- `CDI acumulado`

### Segunda linha

Usa quatro colunas:

- `USD no inicio`
- `USD no fim`
- `Variacao USD/BRL`
- `Variacao % em USD`

### Hierarquia recomendada

A métrica mais importante para a leitura do produto é a variacao % em USD, calculada a partir de `real_usd_return_percentage`. Em um redesign, essa informação pode ganhar mais peso visual, desde que o valor nominal em BRL não vire a conclusão principal da tela.

Os cards percentuais exibem, em detalhe menor, a taxa equivalente anual e mensal do percentual observado no periodo. O texto deve seguir o formato `Equiv.: 12,34% a.a. | 0,97% a.m.` e usar os dias uteis de CDI considerados como denominador.

## Formatação numérica

### BRL

- Prefixo: `R$`
- Duas casas decimais.
- Separador decimal: vírgula.
- Separador de milhar: ponto.
- Exemplo: `R$ 10.000,00`

### USD

- Prefixo: `US$`
- Duas casas decimais.
- Separador decimal: ponto.
- Separador de milhar: vírgula.
- Exemplo: `US$ 2,000.00`

### Percentuais

- Duas casas decimais.
- Separador decimal: vírgula.
- Separador de milhar: ponto.
- Sufixo: `%`
- Exemplo: `12,34%`

### Pontos percentuais

- Duas casas decimais.
- Separador decimal: vírgula.
- Separador de milhar: ponto.
- Sufixo: `p.p.`
- Exemplo: `2,15 p.p.`

### Cotações USD/BRL

- Quatro casas decimais.
- Separador decimal atual do código: ponto.
- Exemplo: `5.1234`

## Notas abaixo das métricas

As notas devem continuar visíveis após o resumo, pois explicam quando a cotação veio de uma data anterior ou quando houve ajuste de período.

### Cotação inicial ou final encontrada na própria data

Template:

`Cotacao {quote_position} encontrada na propria data.`

### Cotação inicial ou final usando data anterior

Template:

`Cotacao {quote_position}: usada a ultima PTAX oficial anterior ({requested_date} -> {effective_date}).`

### Período efetivo igual ao solicitado

`Periodo efetivo de mercado igual ao periodo solicitado.`

### Período efetivo ajustado

Template:

`Periodo efetivo de mercado: {requested_period} -> {effective_period}.`

## Tabela técnica

A tabela técnica aparece depois das métricas e notas. Ela usa largura total do container e oculta o índice.

Colunas:

- `Metrica`
- `Valor`

Linhas:

- `Periodo solicitado`
- `Periodo efetivo de mercado`
- `Cotacao USD/BRL inicial usada`
- `Cotacao USD/BRL final usada`
- `Variacao acumulada do USD/BRL`
- `CDI acima/abaixo do USD/BRL`
- `Dias uteis de CDI considerados`

Em redesign, a tabela pode ser visualmente secundária, mas não deve desaparecer: ela sustenta a auditabilidade do cálculo.

## Gráfico comparativo

O gráfico mostra séries acumuladas ao longo do período efetivo.

### Eixo temporal

- Campo de data: `data`.
- Apenas dias úteis presentes nas séries oficiais devem aparecer.

### Séries visíveis

- `CDI Acumulado (%)`
- `USD/BRL Acumulado (%)`
- `Variacao % em USD`

### Séries disponíveis na base diária

- `data`
- `CDI Acumulado (%)`
- `USD/BRL Acumulado (%)`
- `Variacao % em USD`
- `Capital Corrigido (BRL)`
- `Cotacao USD/BRL`

### Regras visuais recomendadas para o gráfico

- CDI acumulado, variacao do USD/BRL e variacao % em USD devem ser distinguíveis por cor e legenda.
- A série de variacao % em USD deve ser fácil de identificar, pois representa a pergunta central da tela.
- O gráfico deve ocupar a largura disponível.
- Evitar decoração que atrapalhe a leitura de cruzamentos, quedas e divergências entre CDI e dólar.

## Expander da base diária

- Label: `Ver base diaria do grafico`.
- Conteúdo: dataframe com todas as séries derivadas do gráfico.
- Deve usar largura total do container.
- Deve ocultar o índice.

## Expander de metodologia

Label: `Metodologia usada`.

Conteúdo atual:

```text
- O resultado compara o ganho nominal do capital em BRL pelo CDI com a variacao do USD/BRL no mesmo periodo efetivo de mercado.
- O CDI diario vem da serie 12 do SGS/BCB e e acumulado pela regra `data_inicial_efetiva <= data < data_final_efetiva`.
- O USD/BRL usa a cotacao PTAX de venda do Banco Central, obtida pela API Olinda/BCB.
- Calculos, metricas e grafico consideram apenas dias uteis presentes nas series oficiais; fins de semana e feriados nao sao interpolados.
- Datas sem dado oficial sao resolvidas para a ultima data util disponivel. Quando a PTAX nao existe na data efetiva, o app usa a cotacao anterior mais proxima, limitada a 15 dias.
- A diferenca "CDI acima/abaixo do USD/BRL" e medida em pontos percentuais: CDI acumulado menos variacao acumulada do dolar.
- A variacao em USD mede se o capital corrigido pelo CDI compraria mais ou menos dolares no fim do periodo do que comprava no inicio.
- As taxas equivalentes anual e mensal sao anualizacoes/mensalizacoes matematicas do percentual observado, usando 252 e 22 dias uteis, e nao representam previsao.
- O calculo nao considera impostos, taxas, spread cambial, IOF, custos operacionais ou diferencas entre PTAX e cotacoes praticadas por uma instituicao.
- Esta analise e uma comparacao historica com dados oficiais; nao e recomendacao de investimento.
```

## Cores e estados semânticos

A implementação atual usa os estados nativos do Streamlit:

- Positivo: `st.success`.
- Negativo: `st.error`.
- Neutro: `st.info`.
- Estado vazio: `st.info`.
- Erro de domínio, dados ou cache: `st.error`.

Em um redesign, preservar a semântica:

- Verde ou equivalente para CDI acima do USD/BRL.
- Vermelho ou equivalente para CDI abaixo do USD/BRL.
- Azul, cinza ou equivalente para empate/informação.
- Alertas de erro devem ser diferentes de alertas negativos de resultado, quando possível.

## Regras de produto que impactam a interface

- A data inicial válida mínima é 01/07/1994.
- Datas futuras não são permitidas.
- Datas sem dado oficial são resolvidas para a última data útil disponível.
- A UI deve informar quando a data efetiva da cotação difere da data solicitada.
- A busca por cotacao USD/BRL anterior é limitada a 15 dias.
- O CDI usa janela `data_inicial_efetiva <= data < data_final_efetiva`.
- Cálculos, métricas e gráfico consideram apenas dias úteis das séries oficiais.
- O app não considera impostos, taxas, spread cambial, IOF ou custos operacionais.
- A análise não é recomendação de investimento.

## Diretrizes para otimização visual no Stitch

- Manter a primeira dobra focada em título, descrição curta e formulário.
- Evitar transformar a tela em landing page promocional; ela deve continuar sendo uma ferramenta.
- Dar destaque às métricas comparativas logo após o cálculo.
- Não fazer o ganho nominal em BRL parecer a conclusão principal.
- Agrupar métricas de BRL, USD e comparação cambial de forma escaneável.
- Usar densidade visual moderada: a aplicação é analítica, não editorial.
- Priorizar leitura clara em desktop e mobile.
- Preservar todas as mensagens de cotação em data anterior e período efetivo.
- Preservar acesso à tabela técnica e à metodologia.
- Evitar elementos decorativos que confundam a leitura financeira.
- Não introduzir novas regras de cálculo na camada visual.

## Checklist de preservação

Antes de aceitar uma versão otimizada da frontpage, conferir:

- A pergunta central CDI vs USD continua óbvia.
- O formulário contém as mesmas entradas e restrições.
- A data mínima 01/07/1994 continua explícita.
- O estado vazio e o loading continuam presentes.
- Todas as sete métricas atuais continuam acessíveis.
- As notas de cotação em data anterior aparecem quando aplicável.
- A tabela técnica continua disponível.
- O gráfico mantém as três séries principais.
- A base diária do gráfico continua acessível.
- A metodologia continua acessível.
- A tela não promete recomendação de investimento.
