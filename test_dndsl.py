from dndsl import evaluate


class FakeRng:
    def __init__(self, *values):
        self.values = list(values)
        self.calls = []

    def randint(self, a, b):
        self.calls.append((a, b))
        return self.values.pop(0)


def test_single_die_returns_rng_value():
    result = evaluate("1d6", rng=FakeRng(4))

    assert result.total == 4


def test_multiple_dice_are_summed():
    result = evaluate("3d6", rng=FakeRng(2, 5, 6))

    assert result.total == 13


def test_roll_details_lists_each_die():
    result = evaluate("3d6", rng=FakeRng(2, 5, 6))

    assert result.rolls == [2, 5, 6]


def test_rng_called_with_die_faces():
    rng = FakeRng(10)

    evaluate("1d20", rng=rng)

    assert rng.calls == [(1, 20)]


def test_plain_number():
    result = evaluate("5")

    assert result.total == 5


def test_addition():
    result = evaluate("1d6 + 2", rng=FakeRng(4))

    assert result.total == 6


def test_subtraction():
    result = evaluate("1d6 - 2", rng=FakeRng(4))

    assert result.total == 2

def test_left_associativity():
    result = evaluate("10 - 3 - 2")

    assert result.total == 5

def test_addition_keeps_rolls_from_both_operands():
    result = evaluate("1d6 + 1d4", rng=FakeRng(3, 2))

    assert result.rolls == [3, 2]

def test_subtraction_keeps_rolls_from_both_operands():
    result = evaluate("1d6 - 1d4", rng=FakeRng(4, 3))

    assert result.rolls == [4, 3]
