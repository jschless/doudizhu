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
            return("airplane")
    
    return False

def check_straight(cards, min_length=5):
    if len(cards) < min_length:
        return False
    last_card = cards[0]
    for c in cards[1:]:
        if not (c - last_card) == 1:
            return False
        last_card = c
    return True