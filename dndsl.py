import random
from dataclasses import dataclass

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError

parser = Lark.open("dice.lark", rel_to=__file__)


class DiceError(Exception):
    pass


@dataclass
class RollResult:
    total: int
    rolls: list[int]

    def combine(self, other, total):
        return RollResult(total=total, rolls=self.rolls + other.rolls)


@v_args(inline=True)
class Interpreter(Transformer):
    def __init__(self, rng):
        super().__init__()
        self.rng = rng

    def start(self, expr):
        return expr

    def expr(self, term):
        return term

    def add_expr(self, term_1, term_2):
        return term_1.combine(other=term_2, total=term_1.total + term_2.total)

    def sub_expr(self, term_1, term_2):
        return term_1.combine(other=term_2, total=term_1.total - term_2.total)

    def term(self, factor):
        return factor

    def factor(self, roll):
        return roll

    def number(self, value):
        return RollResult(total=int(value), rolls=[])

    def keep_biggest(self, count):
        return lambda rolls: sorted(rolls, reverse=True)[: int(count)]

    def keep_smallest(self, count):
        return lambda rolls: sorted(rolls)[: int(count)]

    def roll(self, quantity, faces, *modifiers):
        rolls = [self.rng.randint(1, int(faces)) for _ in range(int(quantity))]
        kept = rolls
        for modifier in modifiers:
            kept = modifier(kept)
        return RollResult(total=sum(kept), rolls=rolls)


def evaluate(expression, rng=random):
    try:
        tree = parser.parse(expression)
    except LarkError as error:
        raise DiceError(f"invalid expression: {expression!r}") from error

    return Interpreter(rng).transform(tree)
