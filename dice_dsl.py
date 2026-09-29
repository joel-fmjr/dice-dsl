import random
from lark import Lark, Token, UnexpectedInput

parser = Lark.open("dice.lark", rel_to=__file__)


class DiceError(ValueError):
    """Erro semântico: a expressão é sintaticamente válida, mas não faz sentido."""



ROTULO = {"explode": "ex", "keep_biggest": "kb", "keep_smallest": "ks", "reroll": "rr", "min_value": "min", "max_value": "max"}


def validar(tree):
    """Verificação semântica. Roda depois do parse e ANTES de rolar qualquer
    dado, então uma expressão inválida não executa nada.

    Regras (por rolagem NdM seguida de modificadores):
      1. N >= 1 e M >= 1
      2. cada modificador aparece no máximo uma vez
      3. kb e ks não podem aparecer juntos
      4. ex exige M >= 2 (com 1 face todo dado explodiria para sempre)
      5. kb/ks exigem 1 <= n <= N
      6. min exige 1 <= n <= M
      7. max exige 1 <= n <= M
    """
    for roll in tree.find_pred(lambda t: t.data == "roll"):
        qtd = int(roll.children[0])
        lados = int(roll.children[1])
        mods = roll.children[2:]
        nome = f"{qtd}d{lados}"

        if qtd < 1:
            raise DiceError(f"{nome}: precisa de pelo menos 1 dado")
        if lados < 1:
            raise DiceError(f"{nome}: o dado precisa de pelo menos 1 face")

        tipos = [m.data for m in mods]
        for t in set(tipos):
            if tipos.count(t) > 1:
                raise DiceError(f"{nome}: o modificador '{ROTULO[t]}' aparece mais de uma vez")
        if "keep_biggest" in tipos and "keep_smallest" in tipos:
            raise DiceError(f"{nome}: kb e ks não podem ser usados juntos")

        for m in mods:
            if m.data == "explode" and lados < 2:
                raise DiceError(f"{nome}: ex não pode ser usado em dado de 1 face (explodiria para sempre)")
            if m.data in ("keep_biggest", "keep_smallest"):
                n = int(m.children[0])
                if not 1 <= n <= qtd:
                    raise DiceError(f"{nome}: {ROTULO[m.data]}{n} precisa estar entre 1 e {qtd}")
            if m.data == "min_value" or m.data == "max_value":
                n = int(m.children[0])
                if not 1 <= n <= lados:
                    raise DiceError(f"{nome}: min/max{n} precisa estar entre 1 e {lados}")

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


def run_single_roll(node):
    """Executa UMA rolagem (NUMBER 'd' NUMBER modifier*) e registra em
    _detalhes o passo a passo."""
    num_dice = int(node.children[0])
    sides = int(node.children[1])
    modifiers = node.children[2:]

    explode = False
    keep_mode = None
    keep_n = None
    reroll_cmp = None
    reroll_n = None
    min_val = None
    max_val = None

    for m in modifiers:
        if m.data == "explode":
            explode = True
        elif m.data == "keep_biggest":
            keep_mode = "kb"
            keep_n = int(m.children[0])
        elif m.data == "keep_smallest":
            keep_mode = "ks"
            keep_n = int(m.children[0])
        elif m.data == "reroll":
            reroll_cmp = str(m.children[0])
            reroll_n = int(m.children[1])
        elif m.data == "min_value":
            min_val = int(m.children[0])
        elif m.data == "max_value":
            max_val = int(m.children[0])

    trace = []  # lista de (rótulo, snapshot_dos_dados_ou_None)

    def roll_dice():
        return [random.randint(1, sides) for _ in range(num_dice)]

    def apply_reroll(dice):
        if reroll_cmp is None:
            return dice
        out = []
        for d in dice:
            if (reroll_cmp == "<" and d < reroll_n) or (reroll_cmp == ">" and d > reroll_n):
                d = random.randint(1, sides)
            out.append(d)
        return out

    def apply_explode(dice):
        """Devolve (totais, texto). Cada dado que tira o valor máximo rola de
        novo e soma; o texto mostra a cadeia, ex.: [4+3=7, 2]."""
        if not explode:
            return dice, None
        totais, textos = [], []
        for d in dice:
            cadeia = [d]
            while cadeia[-1] == sides:
                cadeia.append(random.randint(1, sides))
            totais.append(sum(cadeia))
            if len(cadeia) > 1:
                textos.append("+".join(map(str, cadeia)) + f"={sum(cadeia)}")
            else:
                textos.append(str(d))
        return totais, "[" + ", ".join(textos) + "]"

    dice = roll_dice()
    trace.append(("dados", list(dice)))

    if reroll_cmp is not None:
        dice = apply_reroll(dice)
        trace.append((f"reroll {reroll_cmp}{reroll_n}", list(dice)))

    if min_val is not None:
        dice = [max(d, min_val) for d in dice]
        trace.append((f"min{min_val}", list(dice)))

    if max_val is not None:
        dice = [min(d, max_val) for d in dice]
        trace.append((f"max{max_val}", list(dice)))

    if keep_n is not None:
        dice = sorted(dice, reverse=(keep_mode == "kb"))[:keep_n]
        trace.append((f"{keep_mode}{keep_n}", list(dice)))

    if explode:
        dice, texto = apply_explode(dice)
        trace.append(("explode", texto))

    total = sum(dice)

    simples = num_dice == 1 and len(modifiers) == 0
    partes = [f"{num_dice}d{sides}"]

    for rotulo, snap in trace:
        partes.append(f"{rotulo}: {snap}" if snap is not None else rotulo)
        
    partes.append(f"total: {total}")
    _detalhes.append((simples, " -> ".join(partes)))

    return total


def run_roll(programa):
    """Imprime o detalhe de TODAS as rolagens, exceto quando a expressão
    é só um único dado sem modificadores (ex.: 1d20)."""
    _detalhes.clear()
    tree = parser.parse(programa)
    validar(tree)
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
        "10d6kl5kh3",
        "4d6 rr<3 kb3 ex min3 ",
        "2d6 + 3 * 2",
        "2d6 * 2 + 3",
        "1d4 * 1d6",
        "4d6kb3rr<3*2-1",
        "(1d10+5+1d6)*2",
        "8d6ks3kb4",
        "4d6ex",
        "4d6min3",
        "4d6max3",
        "1d10min10ex",
    ]

    for ex in exemplos:
        # print(f"### Entrada: {ex}")
        # print(parser.parse(ex).pretty())
        # print("-" * 40)
        print(f"{ex}")
        try:
            resultado = run_roll(ex)
            print(f"  => resultado final: {resultado}\n")
        except UnexpectedInput as e:
            print(f"  erro sintático (rejeitado pela gramática) na coluna {e.column}\n")
        except DiceError as e:
            print(f"  erro semântico: {e}\n")
        break