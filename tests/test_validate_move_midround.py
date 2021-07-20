import pytest
import flaskr

def test_single():
    assert flaskr.game.validate_move(
        {'hand_type': 'single', 'discard_type': 'no-discard', 
        'hand_history': [([3], [], [])]}, 
        [4], []) == ('single', 'no-discard')

def test_lower_single():
    with pytest.raises(RuntimeError):
        assert flaskr.game.validate_move(
            {'hand_type': 'single', 'discard_type': 'no-discard', 
            'hand_history': [([4], [], [])]}, 
            [3], []) == ('single', 'no-discard')