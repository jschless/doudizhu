from enum import Enum
from collections import Counter

def validate_type(cards):
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
            return(f"{len(keys)}-airplane")
    
    return False


def check_straight(cards, min_length=5):
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


discard_moves = {
    'triple': 1, 
    'quad': 2, 
    '2-airplane': 2,
    '3-airplane': 3
}

def validate_discard(cards, move_type):
    if not move_type:
        return False # if the move is not valid, the discard can't be 
    if len(cards) == 0:
        return 'no-discard'        
    n_discards = discard_moves[move_type]
    value_counts = Counter(cards)
    keys, values = value_counts.keys(), value_counts.values()
    if len(set(keys)) == n_discards and len(set(values)) == 1:
        if list(values)[0] == 2:
            return f'{n_discards}-pairs'
        else:
            return f'{n_discards}-singles'
    else:
        return False