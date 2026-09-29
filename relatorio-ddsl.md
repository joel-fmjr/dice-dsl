# D&DSL

Uma linguagem para rolagens de dados de RPG

Descrição do domínio, gramática e análise sintática

## Apresentação

A D&DSL é uma linguagem específica de domínio criada para escrever rolagens de dados usadas em jogos de RPG. A proposta é representar operações comuns, como rolar dados, manter alguns resultados e aplicar bônus, com expressões curtas. Este documento apresenta o objetivo da linguagem, seus tokens, a gramática usada no Lark, exemplos válidos, uma árvore sintática e uma derivação passo a passo.

## 1. Domínio e objetivo

O domínio da D&DSL são as rolagens de dados de RPG. Em uma mesa, uma expressão pode combinar dados com quantidade e número de faces, modificadores e operações aritméticas. Escrever essa lógica em código comum pode ficar comprido e mais difícil de conferir.

A linguagem permite representar uma rolagem como “4d6kb3”, que significa rolar quatro dados de seis faces e manter os três maiores. A mesma notação pode ser interpretada por um programa, que verifica se a expressão está correta, executa os dados e calcula o total.

## 2. Por que esse domínio funciona bem para uma DSL

O domínio tem um vocabulário pequeno e regras objetivas. Cada parte da expressão tem um significado conhecido por quem joga RPG: a quantidade de dados, as faces, os dados que serão mantidos e as condições de rerrolagem. Isso torna possível criar uma linguagem curta sem precisar incluir recursos que não são necessários para esse problema.

A D&DSL poderia ser usada em bots de conversa, em mesas virtuais e em macros ou fichas digitais. Também pode servir como exemplo de estudo de linguagens formais, pois reúne gramática, análise sintática e interpretação.

## 3. Tokens

Os tokens são as unidades que o analisador reconhece na entrada. Os espaços em branco são ignorados, então, por exemplo, “4d6kb3” e “4d6 kb3” podem ser escritos com ou sem espaços.

| Token ou símbolo | Como é reconhecido | Exemplo e significado |
| --- | --- | --- |
| NUMBER | Um ou mais algarismos inteiros, sem sinal. No código, usa common.INT com o nome NUMBER. | 4, 6, 20 |
| COMP | Um dos comparadores < ou >. | rr<3, rr>4 |
| d | Literal que separa quantidade e faces. | 4d6 |
| ex, kb, ks, rr | Palavras-chave dos modificadores. | ex explode; kb mantém os maiores; ks mantém os menores; rr rerrola |
| + - * | Operadores aritméticos. | 2d6 + 3; 2 * 4 |
| ( ) | Delimitadores de agrupamento. | (2d6 + 3) * 2 |
| WS | Espaços em branco; o Lark os ignora. | 4d6 kb3 |

## 4. Gramática em EBNF

A gramática abaixo corresponde às regras do arquivo dice_dsl.py. Os terminais entre aspas são símbolos literais. O asterisco indica zero ou mais repetições, e “|” indica alternativas.

```text
start    ::= expr
expr     ::= expr "+" term | expr "-" term | term
term     ::= term "*" factor | factor
factor   ::= roll | NUMBER | "(" expr ")"
roll     ::= NUMBER "d" NUMBER modifier*
modifier ::= "ex" | "kb" NUMBER | "ks" NUMBER | "rr" COMP NUMBER
COMP     ::= "<" | ">"
NUMBER   ::= ("0".."9")+
```

A regra start exige uma única expressão como programa. A regra expr trata soma e subtração; term trata multiplicação; factor aceita uma rolagem, um número ou uma expressão entre parênteses. Essa organização dá maior precedência à multiplicação do que à soma e à subtração.

A gramática aceita a forma dos modificadores, enquanto a função validar(tree) também confere algumas regras de significado. Por exemplo, ela exige ao menos um dado e uma face, impede repetir o mesmo modificador, não permite usar kb e ks juntos e verifica se a quantidade mantida está entre 1 e a quantidade rolada. Esses casos têm sintaxe válida, mas podem ser rejeitados na validação semântica.

## 5. Exemplos de strings válidas

| Expressão | Interpretação |
| --- | --- |
| 1d20 | Rola um dado de vinte faces. |
| 2d6 + 3 | Rola dois dados de seis faces e soma 3. |
| 4d6kb3 | Rola quatro d6 e mantém os três maiores. |
| 2d20ks1 | Rola dois d20 e mantém o menor. |
| 4d6 rr<3 kb3 | Rerrola uma vez os resultados menores que 3 e mantém os três maiores. |
| 1d6 ex | Rola um d6; cada resultado máximo rola de novo e soma a nova face. |
| (2d6 + 3) * 2 | Agrupa a soma antes de multiplicar por 2. |
| 1d10+5+1d6*2 | Combina duas rolagens, soma e multiplicação. |

As expressões acima foram analisadas pelo parser do Lark e passaram também pela função de validação semântica do código. Como os dados são aleatórios, o total obtido ao executar uma expressão pode mudar a cada rodada.

## 6. Teste da gramática no Lark

O parser é criado a partir da gramática e a chamada parser.parse(texto) verifica se a entrada segue as regras sintáticas. A função run_roll(texto), por sua vez, faz a análise, valida as restrições semânticas e executa a rolagem.

```text
from dice_dsl import parser, run_roll

tree = parser.parse("4d6 rr<3 kb3")  # analisa a sintaxe
resultado = run_roll("4d6 rr<3 kb3")  # valida e executa
```

Entradas como “4d6 rr3”, “d6”, “2d6 +” e “4d6 kh3” são rejeitadas pelo parser porque não seguem a gramática. Já “8d6ks3kb4” tem forma sintática reconhecível, mas a validação semântica rejeita o uso de kb e ks ao mesmo tempo. Assim, o trabalho separa erro de sintaxe de uma combinação que não faz sentido segundo as regras da linguagem.

## 7. Árvore de análise

Para a expressão “4d6kb3 + 2”, o método pretty() produz a seguinte árvore:

```text
start
  add_expr
    expr
      term
        factor
          roll
            4
            6
            keep_biggest  3
    term
      factor  2
```

A estrutura faz sentido: a raiz registra a soma, o ramo esquerdo contém a rolagem com quatro dados de seis faces e o modificador keep_biggest 3, e o ramo direito contém o número 2. Os nomes add_expr e keep_biggest são aliases dados às regras para que a árvore deixe mais claro qual operação foi reconhecida. Os símbolos literais “+” e “d” não aparecem como nós separados nessa árvore.

## 8. Derivação de uma string válida

A seguir, a derivação de “4d6kb3 + 2”. Em cada passo, expandimos o não terminal mais à esquerda. Para facilitar a leitura, modifier* aparece como modifier quando escolhemos exatamente um modificador.

```text
1.  start
2.  expr
3.  expr + term
4.  term + term
5.  factor + term
6.  roll + term
7.  NUMBER d NUMBER modifier* + term
8.  4 d NUMBER modifier* + term
9.  4 d 6 modifier* + term
10. 4 d 6 modifier + term
11. 4 d 6 kb NUMBER + term
12. 4 d 6 kb 3 + term
13. 4 d 6 kb 3 + factor
14. 4 d 6 kb 3 + NUMBER
15. 4 d 6 kb 3 + 2
```

A sequência termina na própria entrada, portanto a expressão pode ser gerada a partir da regra inicial start.

## 9. Decisões de sintaxe

A forma “XdY” foi escolhida por ser curta e reconhecível no contexto de RPG: X representa a quantidade de dados e Y representa as faces. As abreviações kb e ks indicam qual grupo de resultados será mantido, e rr introduz uma condição de rerrolagem. Os comparadores < e > deixam o limite explícito.

A gramática organiza os operadores em níveis. A multiplicação fica em term, que aparece dentro de expr; por isso, “2d6 + 3 * 2” é entendido como “2d6 + (3 * 2)”. Parênteses podem ser usados quando a pessoa quer mudar essa ordem.

Os modificadores podem ser escritos em qualquer ordem. Na execução, o interpretador aplica primeiro rr, depois ex e, por fim, kb ou ks. Cada modificador pode aparecer uma vez, e kb e ks não podem ser combinados. Essa escolha deixa a escrita flexível e mantém a execução previsível.
