import pytest

from dndsl import DiceError, evaluate


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


def test_zero_sided_die_raises_dice_error():
    with pytest.raises(DiceError):
        evaluate("1d0")


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


def test_multiplication():
    result = evaluate("1d6 * 1d4", rng=FakeRng(4, 3))

    assert result.total == 12


def test_multiplication_keeps_rolls_from_both_operands():
    result = evaluate("2d6 * 1d8", rng=FakeRng(4, 3, 8))

    assert result.rolls == [4, 3, 8]


def test_multiplication_takes_precedence_over_addition_on_the_right():
    result = evaluate("3d6 + 3 * 2", rng=FakeRng(4, 3, 2))

    assert result.total == 15


def test_multiplication_takes_precedence_over_addition_on_the_left():
    result = evaluate("3d6 * 2 + 3", rng=FakeRng(4, 3, 2))

    assert result.total == 21


def test_parentheses_change_precedence():
    result = evaluate("(3d6 + 3) * 2", rng=FakeRng(4, 3, 2))

    assert result.total == 24


def test_whitespace_is_ignored():
    compact = evaluate("2d6+1", rng=FakeRng(3, 4))
    spaced = evaluate("  2d6   +   1  ", rng=FakeRng(3, 4))

    assert compact == spaced


def test_invalid_expression_raises_dice_error():
    with pytest.raises(DiceError):
        evaluate("2d")


def test_keep_biggest_counts_only_the_biggest_dice():
    result = evaluate("3d6kb1", rng=FakeRng(2, 5, 3))

    assert result.total == 5


def test_keep_biggest_maintains_rolls():
    result = evaluate("4d6kb1", rng=FakeRng(2, 5, 3, 6))

    assert result.rolls == [2, 5, 3, 6]


def test_keep_biggest_two_counts_the_two_biggest_dice():
    result = evaluate("4d10kb2", rng=FakeRng(2, 8, 3, 10))

    assert result.total == 18


def test_keep_smallest_counts_only_the_smallest_dice():
    result = evaluate("4d4ks1", rng=FakeRng(3, 1, 4, 2))

    assert result.total == 1


def test_keep_smallest_maintains_rolls():
    result = evaluate("4d6ks1", rng=FakeRng(2, 5, 3, 6))

    assert result.rolls == [2, 5, 3, 6]


def test_keep_smallest_two_counts_the_two_smallest_dice():
    result = evaluate("4d10ks2", rng=FakeRng(2, 8, 3, 10))

    assert result.total == 5


def test_min_raises_dice_below_the_minimum():
    result = evaluate("3d6min3", rng=FakeRng(1, 5, 2))

    assert result.total == 11


def test_max_lowers_dice_above_the_maximum():
    result = evaluate("3d6max3", rng=FakeRng(6, 2, 4))

    assert result.total == 8


def test_explode_rolls_an_extra_die_for_each_max_face():
    result = evaluate("2d6ex", rng=FakeRng(6, 3, 4))

    assert result.total == 13


def test_explode_chains_when_the_extra_die_is_also_max():
    result = evaluate("1d6ex", rng=FakeRng(6, 6, 3))

    assert result.total == 15


def test_explode_resolves_a_separate_chain_for_each_max_die():
    result = evaluate("3d6ex", rng=FakeRng(6, 6, 3, 6, 6, 4, 2))

    assert result.total == 33


def test_explode_on_a_one_sided_die_raises_dice_error():
    with pytest.raises(DiceError):
        evaluate("1d1ex", rng=FakeRng(1, 1, 1))


def test_reroll_rerolls_only_dice_below_the_threshold():
    result = evaluate("4d8r<5", rng=FakeRng(6, 2, 8, 5, 6))

    assert result.total == 25


def test_reroll_rerolls_only_dice_above_the_threshold():
    result = evaluate("4d8r>5", rng=FakeRng(6, 8, 6, 5, 2, 5, 3))

    assert result.total == 15


def test_recursive_reroll_repeats_until_the_die_leaves_the_range():
    result = evaluate("2d6rr<3", rng=FakeRng(2, 5, 1, 4))

    assert result.total == 9


def test_recursive_reroll_above_repeats_until_the_die_leaves_the_range():
    result = evaluate("2d6rr>4", rng=FakeRng(5, 2, 6, 3))

    assert result.total == 5


def test_recursive_reroll_that_matches_every_face_raises_dice_error():
    with pytest.raises(DiceError):
        evaluate("1d6rr<7", rng=FakeRng(1, 2, 3))


def test_recursive_reroll_below_is_valid_when_the_max_face_escapes():
    result = evaluate("1d6rr<6", rng=FakeRng(3, 6))

    assert result.total == 6


def test_recursive_reroll_above_zero_matches_every_face_and_raises_dice_error():
    with pytest.raises(DiceError):
        evaluate("1d6rr>0", rng=FakeRng(1, 2, 3))


def test_recursive_reroll_above_is_valid_when_the_min_face_escapes():
    result = evaluate("1d6rr>1", rng=FakeRng(3, 1))

    assert result.total == 1


def test_recursive_reroll_keeps_the_original_rolls():
    result = evaluate("1d6rr<3", rng=FakeRng(1, 4))

    assert result.rolls == [1, 4]


def test_keep_biggest_works_on_dice_capped_by_a_previous_max():
    result = evaluate("2d6max3kb2", rng=FakeRng(5, 5))

    assert result.total == 6


def test_rolls_keep_the_dice_replaced_by_an_earlier_reroll():
    result = evaluate("2d6r<3kb1", rng=FakeRng(1, 5, 4))

    assert result.rolls == [1, 4, 5]
