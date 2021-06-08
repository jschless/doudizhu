from collections import Counter

from .cards import Cards
from .utils import validate_type, validate_discard, discard_moves

class Hand:
    move: Cards
    discard: Cards
    move_type: str 
    discard_type: str 
    player: int
    player_name: str

    def __init__(self, available_cards, last_hand=None):
        discard_move = []
        discard_type = None
        print('Your cards:', available_cards)
        if last_hand:
            print('The last hand: ', last_hand)
        while True:
            move = input("enter move separated by commas, write pass to pass:")

            if move == "pass":
                if last_hand is None:
                    raise RuntimeError("You cannot pass on the first move")
                else:
                    move = []
                    break

            if move == "exit":
                exit()

            try:
                move = [int(x) for x in move.split(',')]
                move_type = validate_type(move)

                c1, c2 = Counter(move), Counter(available_cards)
                for k, n in c1.items():
                    if n > c2[k]:
                        raise RuntimeError("Tried to play card you don't have, cheater")

                if move_type is False:
                    raise RuntimeError("Invalid move: not a valid hand")

                if last_hand is not None and not last_hand.move_type == move_type:
                    raise RuntimeError("Invalid move: move did not fit hand category")

                if last_hand is not None and last_hand >= move:
                    raise RuntimeError("Tried to play weaker hand")

                if (
                    (last_hand is None and move_type in discard_moves) 
                    or (last_hand is not None and last_hand.discard_type is not None)
                    or (last_hand is not None and last_hand.discard_type != "no-discard")
                ):
                    discard_move = input("enter cards to discard separeted by commas:")
                    discard_move = [int(x) for x in discard_move.split(',')]
                    discard_type = validate_discard(discard_move, move_type)
                    if discard_type is False:
                        raise RuntimeError("Invalid discard")

                    if last_hand is not None and discard_type != last_hand.discard_type:
                        raise RuntimeError("Invalid discard: did not match hand discard category")

                break 
            except Exception as e:
                print(e, 'invalid move, try again')
                continue

        self.move = Cards(move)
        self.move_type = move_type 
        self.discard = Cards(discard_move)
        self.discard_type = discard_type

    def __ge__(self, other):
        return sum(self) >= sum(other)

    def __str__(self):
        ans = f"Move Type: {self.move_type}, discard: {self.discard_type}\n"
        if len(self.move) == 0:
            ans += "PASS"
        else:
            ans += "Main move: " + str(self.move) + "\n"
            if len(self.discard) > 0:
                ans += 'Discard: ' + str(self.discard)
        return ans