import random
from collections import Counter

from .utils import validate_type, validate_discard, discard_moves
from .cards import Cards
from .hand import Hand

class Player:
    name: str
    user_id: str
    cards: list
    score: int
    is_turn: bool
    bid: int
    test: bool

    def __init__(self, name, user_id, test=False):
        if test:
            random.seed(1)
        self.name = name
        self.user_id = user_id
        self.cards = None
        self.score = 0
        self.test = test

    def __dict__(self):
        return {'username': self.name, 
                'cards': self.cards, 
                'score': self.score}

    def flip_card_over(self):
        # choose a random card and reveal it
        print(self.name, 'bids first, he got the flipped over card')
        pass
    
    def play(self, last_hand):
        print('It is now ', self.name, '\'s turn')

        hand = Hand(self.cards, last_hand)

        for c in [*hand.move, *hand.discard]:
            self.cards.remove(c)

        print('Your move:')
        print(hand)
        return hand

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