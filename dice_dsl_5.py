import random
from lark import Lark, Token

dice_grammar = r"""
    start: expr

    expr: expr "+" term   -> add_expr
        | expr "-" term   -> sub_expr
        | term

    term: term "*" factor -> mul_expr
        | factor

    factor: roll
          | NUMBER
          | "(" expr ")"

    roll: explode

    explode: explode "ex"        -> explode
            | keep

    keep: keep "kb" NUMBER          -> keep_biggest
          | keep "ks" NUMBER          -> keep_smallest
          | reroll

    reroll: reroll "rr" COMP NUMBER -> reroll
            | base

    base: NUMBER "d" NUMBER

    COMP: "<" | ">"

    %import common.INT -> NUMBER
    %import common.WS
    %ignore WS
"""

parser = Lark(dice_grammar)

_detalhes = []


def eval_node(node):
    """Percorre a árvore e calcula o valor final da expressão."""
    if isinstance(node, Token):
        return int(node)

    if node.data in ("start", "expr", "term", "factor"):
        return eval_node(node.children[0])
    if node.data == "add_expr":
        return eval_node(node.children[0]) + eval_node(node.children[1])
    if node.data == "sub_expr":
        return eval_node(node.children[0]) - eval_node(node.children[1])
    if node.data == "mul_expr":
        return eval_node(node.children[0]) * eval_node(node.children[1])
    if node.data == "roll":
        return run_single_roll(node)

    raise ValueError(f"Nó desconhecido na árvore: {node.data}")


def eval_dice(node):
    """Avalia uma rolagem DE BAIXO PRA CIMA: cada camada da gramática
    (base -> reroll -> explode -> keep) recebe os dados da camada
    de baixo e devolve os dados transformados.

    Devolve (dados, lados, trace, qtd_dados, qtd_modificadores)."""
    tipo = node.data

    # camadas sem modificador: só repassam o filho
    if tipo in ("roll", "keep", "explode", "reroll"):
        return eval_dice(node.children[0])

    # base: onde os dados de fato são rolados
    if tipo == "base":
        qtd = int(node.children[0])
        lados = int(node.children[1])
        dados = [random.randint(1, lados) for _ in range(qtd)]
        return dados, lados, [("dados", list(dados))], qtd, 0

    # daqui pra baixo, o primeiro filho é a camada de baixo
    dados, lados, trace, qtd, mods = eval_dice(node.children[0])
    mods += 1

    if tipo == "reroll":
        cmp_ = str(node.children[1])
        limite = int(node.children[2])
        novos = []
        for d in dados:
            if (cmp_ == "<" and d < limite) or (cmp_ == ">" and d > limite):
                d = random.randint(1, lados)
            novos.append(d)
        trace.append((f"rr {cmp_}{limite}", list(novos)))
        return novos, lados, trace, qtd, mods

    if tipo == "explode":
        totais, textos = [], []
        for d in dados:
            cadeia = [d]
            while cadeia[-1] == lados:
                cadeia.append(random.randint(1, lados))
            totais.append(sum(cadeia))
            if len(cadeia) > 1:
                textos.append("+".join(map(str, cadeia)) + f"={sum(cadeia)}")
            else:
                textos.append(str(d))
        trace.append(("explode", "[" + ", ".join(textos) + "]"))
        return totais, lados, trace, qtd, mods

    if tipo in ("keep_biggest", "keep_smallest"):
        n = int(node.children[1])
        maiores = tipo == "keep_biggest"
        mantidos = sorted(dados, reverse=maiores)[:n]
        rotulo = f"{'kb' if maiores else 'ks'}{n}"
        trace.append((rotulo, list(mantidos)))
        return mantidos, lados, trace, qtd, mods

    raise ValueError(f"Camada desconhecida na rolagem: {tipo}")


def run_single_roll(node):
    """Executa UMA rolagem e registra em _detalhes o passo a passo."""
    dados, lados, trace, qtd, mods = eval_dice(node)
    total = sum(dados)

    simples = qtd == 1 and mods == 0
    partes = [f"{qtd}d{lados}"]
    for rotulo, snap in trace:
        partes.append(f"{rotulo}: {snap}")
    partes.append(f"total: {total}")
    _detalhes.append((simples, " -> ".join(partes)))

    return total


def run_roll(programa):
    """Imprime o detalhe de TODAS as rolagens, exceto quando a expressão
    é só um único dado sem modificadores (ex.: 1d20)."""
    _detalhes.clear()
    tree = parser.parse(programa)
    total = eval_node(tree)

    composta = any(tree.find_pred(
        lambda t: t.data in ("add_expr", "sub_expr", "mul_expr")))
    todas_simples = all(simples for simples, _ in _detalhes)

    if composta or not todas_simples:
        for _, linha in _detalhes:
            print(f"  {linha}")

    return total


if __name__ == "__main__":
    exemplos = [
        "4d6 rr<3 kb3 ex ",
        "(2d6 + 3) * 2",
        "1d10+5+1d6*2",
        "8d6ks4kb3",
        "4d6kb4rr<3kb3",
    ]

    for ex in exemplos:
        print(f"### Entrada: {ex}")
        print(parser.parse(ex).pretty())
        print("-" * 40)
        print(f"{ex}")
        resultado = run_roll(ex)
        print(f"  => resultado final: {resultado}\n")
        break