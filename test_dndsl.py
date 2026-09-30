from dndsl import evaluate


class FakeRng:
    def __init__(self, *values):
        self.values = list(values)

    def randint(self, a, b):
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
