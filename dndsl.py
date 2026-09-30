import random
from dataclasses import dataclass

from lark import Lark, Transformer, v_args

parser = Lark.open("dice.lark", rel_to=__file__)


@dataclass
class RollResult:
    total: int
    rolls: list[int]


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
        total = term_1.total + term_2.total
        return RollResult(total=total, rolls=[])

    def term(self, factor):
        return factor

    def factor(self, roll):
        return roll

    def number(self, value):
        return RollResult(total=int(value), rolls=[])

    def roll(self, quantity, faces):
        rolls = [self.rng.randint(1, int(faces)) for _ in range(int(quantity))]
        return RollResult(total=sum(rolls), rolls=rolls)


def evaluate(expression, rng=random):
    return Interpreter(rng).transform(parser.parse(expression))
