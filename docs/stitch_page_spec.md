# Briefing para Stitch: pagina web Armadilha do CDI

## Objetivo da pagina

Criar uma interface web clara, analitica e responsiva para o produto **Armadilha do CDI**.

A pagina nao deve parecer uma calculadora generica de renda fixa. A leitura central e:

> Se um capital ficou aplicado em CDI entre duas datas, a posicao relativa em dolar melhorou, piorou ou apenas pareceu ter melhorado em reais?

O foco visual deve contrastar:

- crescimento nominal em BRL;
- variacao do USD/BRL;
- ganho ou perda de poder relativo em USD.

## Tom visual

- Aparencia: produto financeiro analitico, confiavel e direto.
- Sensacao: sobrio, moderno, tecnico sem parecer complexo demais.
- Evitar: visual de landing page promocional, excesso de decoracao, gradientes chamativos ou cards muito arredondados.
- Priorizar: leitura rapida, hierarquia clara, comparacao entre metricas e destaque para o resultado em USD.

## Estrutura da primeira tela

### Cabecalho

Titulo principal:

```text
Armadilha do CDI
```

Subtitulo:

```text
Compare o crescimento nominal em reais com a variacao do dolar e descubra se o CDI preservou seu poder relativo em USD.
```

O cabecalho deve ocupar pouco espaco vertical. A aplicacao deve aparecer ja na primeira dobra, sem hero grande.

### Painel de entrada

Criar uma area de formulario com tres campos na mesma linha em desktop e empilhados no mobile:

1. **Data inicial**
   - controle de data;
   - formato visual `DD/MM/AAAA`.

2. **Data final**
   - controle de data;
   - formato visual `DD/MM/AAAA`.

3. **Valor inicial investido**
   - campo monetario em BRL;
   - exemplo: `R$ 10.000,00`.

Botao primario:

```text
Analisar periodo
```

Microcopy abaixo ou acima do formulario:

```text
Informe datas a partir de 01/07/1994. Datas sem dado oficial usam a ultima data util disponivel.
```

## Estado inicial

Antes da primeira analise, mostrar uma mensagem discreta:

```text
Preencha o formulario e clique em Analisar periodo para gerar o resultado.
```

Essa mensagem deve ser secundaria, sem ocupar o centro da pagina inteira.

## Estado de carregamento

Enquanto os dados sao buscados:

```text
Buscando dados do Banco Central e calculando o resultado...
```

Usar indicador de loading simples.

## Area de resultado

Depois da analise, a pagina deve mostrar primeiro o resumo analitico.

### Grupo 1: resultado em BRL

Tres metricas lado a lado:

- **Valor inicial**
  - exemplo: `R$ 10.000,00`
- **Valor final com CDI**
  - exemplo: `R$ 12.430,51`
- **CDI acumulado**
  - exemplo: `24,31%`

### Grupo 2: leitura em USD

Tres metricas lado a lado:

- **USD no inicio**
  - exemplo: `US$ 2,000.00`
- **USD no fim com CDI**
  - exemplo: `US$ 1,850.00`
- **Ganho real em USD**
  - exemplo positivo: `+7,69%`
  - exemplo negativo: `-4,82%`

A metrica **Ganho real em USD** deve ser o principal destaque visual do resultado.

Regras de cor sugeridas:

- positivo: verde contido;
- negativo: vermelho contido;
- proximo de zero: cinza ou amarelo discreto.

Nao usar cores fluorescentes.

## Notas de transparencia

Abaixo das metricas, mostrar notas curtas quando houver ajuste de data:

```text
Cotacao inicial com fallback: 12/10/2024 -> 11/10/2024.
Cotacao final encontrada na propria data.
Periodo efetivo de mercado: 12/10/2024 a 12/10/2025 -> 11/10/2024 a 10/10/2025.
```

Essas notas devem ser visiveis, mas secundarias.

## Tabela tecnica resumida

Incluir tabela compacta com duas colunas:

| Metrica | Valor |
| --- | --- |
| Periodo solicitado | 01/01/2024 a 01/01/2025 |
| Periodo efetivo de mercado | 29/12/2023 a 31/12/2024 |
| Cotacao USD/BRL inicial usada | 4,8521 |
| Cotacao USD/BRL final usada | 6,1923 |
| Dias uteis de CDI considerados | 252 |

A tabela deve ser densa e legivel, sem parecer uma planilha pesada.

## Grafico comparativo

Titulo:

```text
Grafico comparativo
```

Grafico de linhas com tres series:

- `CDI Acumulado (%)`
- `USD Acumulado (%)`
- `Ganho Real em USD (%)`

Recomendacao visual:

- CDI: azul;
- USD: cinza escuro ou grafite;
- ganho real em USD: verde quando positivo e vermelho quando negativo, se a ferramenta permitir; caso contrario, usar uma cor unica de destaque.

O grafico deve comunicar rapidamente se a curva do dolar superou o CDI no periodo.

Incluir acao secundaria:

```text
Ver base diaria do grafico
```

Essa acao pode abrir uma tabela expansivel.

## Bloco de metodologia

Usar bloco recolhivel ou secao secundaria no fim:

Titulo:

```text
Metodologia usada
```

Conteudo:

- Datas sem dado oficial sao resolvidas para o ultimo dia util disponivel.
- O CDI e acumulado pela regra `data_inicial_efetiva <= data < data_final_efetiva`.
- O dolar usa a cotacao PTAX de venda do Banco Central.
- Se nao houver cotacao na data exata, o app busca a ultima cotacao anterior em ate 15 dias.
- O grafico considera apenas dias uteis presentes nas series oficiais.
- O ganho real em USD mede a variacao do capital corrigido pelo CDI quando convertido para dolar no fim do periodo.

## Tratamento de erros

Exibir mensagens claras proximas ao formulario ou no topo da area de resultado.

Casos:

- data final anterior ou igual a data inicial;
- valor inicial invalido;
- ausencia de dados de mercado;
- falha inesperada ao consultar dados.

Tom das mensagens: direto, sem linguagem tecnica excessiva.

## Layout responsivo

### Desktop

- Largura ampla.
- Formulario em tres colunas.
- Metricas em duas linhas de tres colunas.
- Grafico ocupando largura total.
- Tabela tecnica abaixo das notas ou ao lado do grafico apenas se houver espaco suficiente.

### Tablet

- Formulario pode usar duas colunas e quebrar o valor para a linha seguinte.
- Metricas podem usar duas colunas.

### Mobile

- Formulario empilhado.
- Metricas em uma coluna ou cards compactos de largura total.
- Grafico com boa altura e legenda legivel.
- Tabela com rolagem horizontal se necessario.

## Componentes esperados

- Header compacto.
- Formulario de parametros.
- Botao primario.
- Estado vazio.
- Estado de carregamento.
- Cards ou blocos de metricas.
- Notas de fallback.
- Tabela tecnica.
- Grafico de linhas.
- Secao recolhivel de metodologia.
- Mensagens de erro.

## Diretrizes de conteudo

Usar os seguintes termos de forma consistente:

- `BRL`
- `USD`
- `USD/BRL`
- `CDI acumulado`
- `Ganho real em USD`
- `Periodo efetivo de mercado`
- `Cotacao PTAX de venda`

Evitar termos como:

- lucro garantido;
- rentabilidade real no sentido inflacionario;
- simulador de investimentos completo;
- recomendacao de investimento.

## Prompt curto para colar no Stitch

```text
Crie uma interface web responsiva para "Armadilha do CDI", uma ferramenta financeira que compara o crescimento nominal de um capital em BRL aplicado no CDI com a variacao do USD/BRL, mostrando se houve ganho ou perda de poder relativo em USD. A tela deve ser sobria, analitica e direta, sem parecer landing page promocional. Inclua cabecalho compacto, formulario com data inicial, data final e valor inicial em BRL, botao "Analisar periodo", estado vazio, loading, resumo com seis metricas, destaque principal para "Ganho real em USD", notas de fallback de cotacao, tabela tecnica, grafico de linhas com CDI acumulado, USD acumulado e ganho real em USD, e bloco recolhivel de metodologia. Use layout amplo em desktop e empilhado no mobile. O produto deve enfatizar que o resultado principal nao e apenas rendimento em reais, mas preservacao ou perda de poder relativo em dolar.
```
