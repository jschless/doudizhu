from collections import Counter
from typing import List, Union


def validate_type(cards: List):
    """Returns hand type for submitted hand


    Args:
        cards ([List]): a list of integers represent cards

    Returns:
        String: Returns the name of the hand type
        False: Returns false if the submitted move is invalid
    """
    cards = sorted(cards)
    n_cards = len(cards)
    if n_cards == 1:
        return "single"

    if n_cards == 2:
        if cards[0] == 16 and cards[1] == 17:
            return "rocket"
        elif cards[0] == cards[1]:
            return "pair"
        else:
            return False

    if n_cards == 3 and len(set(cards)) == 1:
        return "triple"

    if n_cards == 4 and len(set(cards)) == 1:
        return "quad"

    if check_straight(cards):
        return f"{len(cards)}-straight"

    # check pairs and triples
    value_counts = Counter(cards)
    keys = list(value_counts.keys())
    vals = list(set(value_counts.values()))
    if len(vals) == 1 and vals[0] == 2:
        if check_straight(keys, min_length=3):
            return f"{len(keys)}-pair-straight"

    if len(vals) == 1 and vals[0] == 3:
        if check_straight(keys, min_length=2):
            return f"{len(keys)}-airplane"

    return False


def check_straight(cards: List, min_length: int = 5) -> bool:
    """Checks if a hand is a straight

    Args:
        cards (list): A list of ints representing the hand
        min_length (int, optional): How long the straight must be. Defaults to 5.

    Returns:
        bool: True if it is a valid straight, else false
    """
    if len(cards) < min_length:
        return False

    if 15 in cards or 16 in cards or 17 in cards:
        # can't have a 2 or joker in a straight
        return False
    last_card = cards[0]
    for c in cards[1:]:
        if not (c - last_card) == 1:
            return False
        last_card = c
    return True


discard_moves = {"triple": 1, "quad": 2, "2-airplane": 2, "3-airplane": 3}


def validate_discard(cards: List, move_type: str) -> Union[str, bool]:
    """Validates a discard move

    Args:
        cards (List): List of integers corresponding to cards
        move_type (str): Type of move the discard was attempted with

    Returns:
        Union[str, bool]: String representing type of discard or False if invalid
    """
    if not move_type:
        return False  # if the move is not valid, the discard can't be
    if len(cards) == 0:
        return "no-discard"
    n_discards = discard_moves[move_type]
    value_counts = Counter(cards)
    keys, values = value_counts.keys(), value_counts.values()
    if len(set(keys)) == n_discards and len(set(values)) == 1:
        if list(values)[0] == 2:
            return f"{n_discards}-pairs"
        else:
            return f"{n_discards}-singles"
    else:
        return False


def possible_valid_moves(cards: List, move_type: str) -> List[List]:
    """Returns a list of possible moves that can be made

    Args:
        cards (List): list of possible cards to make hand out of
        move_type (str): move type

    Returns:
        List[List]: list of possible moves
    """
    pass
