import random
from collections import Counter
from utils import validate_type, validate_discard, discard_moves
from cards import Cards

class Player:
    name: str
    cards: list
    score: int
    is_turn: bool
    bid: int
    test: bool

    def __init__(self, name, test=False):
        if test:
            random.seed(1)
        self.name = name
        self.cards = None
        self.score = 0
        self.test = test

    def flip_card_over(self):
        # choose a random card and reveal it
        print(self.name, 'bids first, he got the flipped over card')
        pass
    
    def play(self, last_hand, hand_move_type, hand_discard_type, first_move=False):
        print('beginning', self.name, 'turn')
        print('last_hand', last_hand, 'move_type', hand_move_type)
        print("cards:", self.cards)

        discard_move = []
        discard_type = None

        while True:
            move = input("enter move separated by commas, write pass to pass:")
            if move == "pass":
                if first_move:
                    raise RuntimeError("You cannot pass on the first move")
                else:
                    return None
            if move == "exit":
                exit()
            try:
                move = [int(x) for x in move.split(',')]
                print('your move:', move)
                move_type = validate_type(move)

                c1, c2 = Counter(move), Counter(self.cards)
                for k, n in c1.items():
                    if n > c2[k]:
                        raise RuntimeError("Tried to play card you don't have, cheater")

                if move_type is False:
                    raise RuntimeError("Invalid move: not a valid hand")

                if not first_move and not hand_move_type == move_type:
                    raise RuntimeError("Invalid move: move did not fit hand category")

                if not first_move and sum(last_hand) >= sum(move):
                    raise RuntimeError("Tried to play weaker hand")

                if (first_move and move_type in discard_moves) or hand_discard_type is not None:
                    discard_move = input("enter cards to discard separeted by commas:")
                    discard_move = [int(x) for x in discard_move.split(',')]
                    discard_type = validate_discard(discard_move, move_type)
                    if discard_type is False:
                        raise RuntimeError("Invalid discard")

                    if not first_move and not discard_type == hand_discard_type:
                        raise RuntimeError("Invalid discard: did not match hand discard category")

                break 
            except Exception as e:
                print(e, 'invalid move, try again')
                continue

        for c in [*move, *discard_move]:
            self.cards.remove(c) 

        if first_move:
            return move, move_type, discard_type
        else:
            return move

    def get_bid(self, current_bid):
        # bid must be higher than current bid or pass
        bid = None
        if self.test:
            bid = random.randint(0,3)
        else:
            print('Your cards: ', self.cards)
            while True:
                try:
                    bid = int(input("Enter your bid: "))
                except ValueError:
                    print('Must be a number between 0 and 3')
                if bid < 0 or bid > 3:
                    print("Must be between 0 and 3, type 0 to pass")
                    continue
                else: 
                    break 

        if bid > current_bid:
            print(self.name, 'bid', bid)
            return bid
        else:
            print(self.name, 'passed')
            return -1