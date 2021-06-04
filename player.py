import random
from utils import validate_type

class Player:
    name: str
    cards: list
    score: int
    is_turn: bool
    bid: int

    def __init__(self, name):
        self.name = name
        self.cards = []
        self.score = 0

    def flip_card_over(self):
        # choose a random card and reveal it
        pass
    
    def play(self, last_hand, move_type):
        print('beginning', self.name, 'turn')
        print('last_hand', last_hand, 'move_type', move_type)
        print("cards:", self.cards)
        move = input("enter move separated by commas:")
        move = [int(x) for x in move.split(',')]
        print('your move:', move)
        your_move_type = validate_type(move)
        print('move type:', your_move_type)
        if move_type is None and your_move_type is not None:
            for c in move:
                self.cards.remove(c)
        elif your_move_type == move_type:
            for c in move:
                self.cards.remove(c)
        else:
            move = None
            print('invalid move')

        # discard_moves = ['triple', 'quad', 'airplane']
        # if move_type in discard_moves:
        #     print("cards:", self.cards)
        #     move = input("enter cards to discard separeted by commas:")

        print('hand after move', self.cards)
        return move, your_move_type

    def get_bid(self, current_bid):
        # bid must be higher than current bid or pass
        bid = random.randint(0,3)
        if bid > current_bid:
            print(self.name, 'bid', bid)
            return bid
        else:
            print(self.name, 'passed')
            return -1