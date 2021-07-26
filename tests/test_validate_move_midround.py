import pytest

def test_single(test_game):
    test_game.hand_type = 'single'
    test_game.discard_type = 'no-discard'
    test_game.hand_history = [([3], [], [])]
    assert test_game.validate_move([4], []) == ('single', 'no-discard')

def test_lower_single(test_game):
    test_game.hand_type = 'single'
    test_game.discard_type = 'no-discard'
    test_game.hand_history = [([3], [], [])]
    with pytest.raises(RuntimeError):
        assert test_game.validate_move([3], []) == ('single', 'no-discard')