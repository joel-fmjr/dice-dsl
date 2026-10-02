import operator
import random
from dataclasses import dataclass

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, VisitError

parser = Lark.open("dice.lark", rel_to=__file__)


COMPARATORS = {"<": operator.lt, ">": operator.gt}


def _criterion(comp, threshold):
    compare = COMPARATORS[str(comp)]
    return lambda roll: compare(roll, int(threshold))


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

    def mul_expr(self, term_1, term_2):
        return term_1.combine(other=term_2, total=term_1.total * term_2.total)

    def term(self, factor):
        return factor

    def factor(self, roll):
        return roll

    def number(self, value):
        return RollResult(total=int(value), rolls=[])

    def keep_biggest(self, count):
        return lambda rolls, die: (
            rolls,
            sorted(rolls, reverse=True)[: int(count)],
        )

    def keep_smallest(self, count):
        return lambda rolls, die: (rolls, sorted(rolls)[: int(count)])

    def min_value(self, minimum):
        return lambda rolls, die: (rolls, [max(roll, int(minimum)) for roll in rolls])

    def max_value(self, maximum):
        return lambda rolls, die: (rolls, [min(roll, int(maximum)) for roll in rolls])

    def explode(self):
        def apply(rolls, die):
            if die.faces == 1:
                raise DiceError("Can not explode a one-sided die")

            history = []
            for roll in rolls:
                history.append(roll)
                while roll == die.faces:
                    roll = die.roll()
                    history.append(roll)
            return history, history

        return apply

    def reroll(self, comp, threshold):
        criterion = _criterion(comp, threshold)

        def apply(rolls, die):
            history, counted = [], []
            for roll in rolls:
                history.append(roll)
                if criterion(roll):
                    roll = die.roll()
                    history.append(roll)
                counted.append(roll)
            return history, counted

        return apply

    def recursive_reroll(self, comp, threshold):
        criterion = _criterion(comp, threshold)

        def apply(rolls, die):
            if all(criterion(face) for face in range(1, die.faces + 1)):
                raise DiceError("Recursive reroll would never stop")

            history, counted = [], []
            for roll in rolls:
                history.append(roll)
                while criterion(roll):
                    roll = die.roll()
                    history.append(roll)
                counted.append(roll)
            return history, counted

        return apply

    def roll(self, quantity, faces, *modifiers):
        if not int(faces):
            raise DiceError("Can not roll a zero-sided die")

        die = Die(faces=int(faces), rng=self.rng)
        history = counted = [die.roll() for _ in range(int(quantity))]

        for modifier in modifiers:
            history, counted = modifier(counted, die)

        return RollResult(total=sum(counted), rolls=history)


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
