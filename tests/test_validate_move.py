import pytest

@pytest.mark.parametrize("hand", [[x] for x in range(3,18)])
def test_start_single(hand, test_game):
    assert test_game.validate_move(hand, []) == ('single', 'no-discard')

@pytest.mark.parametrize("hand", [[x,x] for x in range(3,16)])
def test_start_pair(hand, test_game):
    assert test_game.validate_move(hand, []) == ('pair', 'no-discard')

@pytest.mark.parametrize("hand", [[x]*3 for x in range(3,16)])
def test_start_triple(hand, test_game):
    assert test_game.validate_move(hand, []) == ('triple', 'no-discard')

@pytest.mark.parametrize("hand", [[x]*4 for x in range(3,16)])
def test_start_quad(hand, test_game):
    assert test_game.validate_move(hand, []) == ('quad', 'no-discard')

@pytest.mark.parametrize("hand", [[x]*4 for x in range(3,16)])
def test_start_quad_with_attachments(hand, test_game):
    assert test_game.validate_move(hand, [3,3,4,4]) == ('quad', '2-pairs')

def test_start_rocket(test_game):
    assert test_game.validate_move([16,17], []) == ('rocket', 'no-discard')

@pytest.mark.parametrize("hand", [[i,i,i,i+1,i+1,i+1] for i in range(3,13)])
def test_two_airplane_no_discard(hand, test_game):
    assert test_game.validate_move(hand, []) == ('2-airplane', 'no-discard')

@pytest.mark.parametrize("hand", [[i,i,i,i+1,i+1,i+1] for i in range(3,13)])
# @pytest.mark.parametrize("discard", [[i, i, i+1, i+1] for i in range(3,16)])
def test_two_airplane_two_pair_discard(hand, test_game):
    assert test_game.validate_move(hand, [4,4, 10,10]) == ('2-airplane', '2-pairs')

@pytest.mark.parametrize("hand", [[i,i,i,i+1,i+1,i+1] for i in range(3,13)])
def test_two_airplane_two_singles_discard(hand, test_game):
    assert test_game.validate_move(hand, [3,4]) == ('2-airplane', '2-singles')

@pytest.mark.parametrize("hand", [[i,i,i,i+1,i+1,i+1] for i in range(3,13)])
def test_two_airplane_two_singles_discard(hand, test_game):
    with pytest.raises(RuntimeError):
        assert test_game.validate_move(hand, [3,3,4]) == ('2-airplane', '2-singles')

@pytest.mark.parametrize("hand", [[3,3,4,4,5,5], [10,10,11,11,12,12]])
def test_three_pair_straight(hand, test_game):
    assert test_game.validate_move(hand, []) == ('3-pair-straight', 'no-discard')

@pytest.mark.parametrize("hand", [
    [3,3,4,4,5,5,6,6,7,7], [10,10,11,11,12,12,13,13,14,14]
    ])
def test_five_pair_straight(hand, test_game):
    assert test_game.validate_move(hand, []) == ('5-pair-straight', 'no-discard')

@pytest.mark.parametrize("hand", [list(range(i, i+5)) for i in range(3, 11)])
def test_five_straight(hand, test_game):
    assert test_game.validate_move(hand, []) == ('5-straight', 'no-discard')

@pytest.mark.parametrize("hand", [list(range(i, i+6)) for i in range(3, 10)])
def test_five_straight(hand, test_game):
    assert test_game.validate_move(hand, []) == ('6-straight', 'no-discard')