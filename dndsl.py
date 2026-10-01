import random
from dataclasses import dataclass

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, VisitError

parser = Lark.open("dice.lark", rel_to=__file__)


class DiceError(Exception):
    pass


@dataclass
class Die:
    faces: int
    rng: object

    def roll(self):
        return self.rng.randint(1, self.faces)


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
        return lambda rolls, die: sorted(rolls, reverse=True)[: int(count)]

    def keep_smallest(self, count):
        return lambda rolls, die: sorted(rolls)[: int(count)]

    def min_value(self, minimum):
        return lambda rolls, die: [max(roll, int(minimum)) for roll in rolls]

    def max_value(self, maximum):
        return lambda rolls, die: [min(roll, int(maximum)) for roll in rolls]

    def explode(self):
        def apply(rolls, die):
            if die.faces == 1:
                raise DiceError("Can not explode a one-sided die")

            extra = []
            for roll in rolls:
                while roll == die.faces:
                    roll = die.roll()
                    extra.append(roll)
            return rolls + extra

        return apply

    def reroll(self, comp, threshold):
        if comp != "<":
            return lambda rolls, die: [
                die.roll() if roll > int(threshold) else roll for roll in rolls
            ]

        return lambda rolls, die: [
            die.roll() if roll < int(threshold) else roll for roll in rolls
        ]

    def recursive_reroll(self, comp, threshold):
        if comp != "<":
            raise NotImplementedError

        def apply(rolls, die):
            new_rolls = []
            for roll in rolls:
                while roll < int(threshold):
                    roll = die.roll()
                new_rolls.append(roll)
            return new_rolls

        return apply

    def roll(self, quantity, faces, *modifiers):
        if not int(faces):
            raise DiceError("Can not roll a zero-sided die")

        die = Die(faces=int(faces), rng=self.rng)
        rolls = [die.roll() for _ in range(int(quantity))]
        kept = rolls

        for modifier in modifiers:
            kept = modifier(kept, die)
        return RollResult(total=sum(kept), rolls=rolls)


def evaluate(expression, rng=random):
    try:
        tree = parser.parse(expression)
    except LarkError as error:
        raise DiceError(f"invalid expression: {expression!r}") from error

    try:
        return Interpreter(rng).transform(tree)
    except VisitError as error:
        if isinstance(error.orig_exc, DiceError):
            raise error.orig_exc from error
        raise
