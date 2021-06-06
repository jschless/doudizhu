import random
from player import Player
from cards import Cards

class Round:
    players: list
    blind: list
    leading_player: int
    finished: bool

    def __init__(self, players):
        self.players = players
        deck = []
        for i in range(4):
            deck += list(range(3, 16))

        # add jokers 
        deck.append(16)
        deck.append(17)

        random.shuffle(deck)

        self.players[0].cards = Cards(sorted(deck[:17]))
        self.players[1].cards = Cards(sorted(deck[17:34]))
        self.players[2].cards = Cards(sorted(deck[34:51]))
        self.blind = Cards(sorted(deck[51:]))

        self.leading_player = random.randint(0,2)
        self.players[self.leading_player].flip_card_over()

    def start_round(self):
        self.leading_player = self.run_bidding()
        if self.leading_player is None:
            print('reshuffle')
            exit()
        
        print('blind is', self.blind)
        self.players[self.leading_player].cards += self.blind

        round_finished = False
        current_player = self.leading_player

        while not round_finished:
            # do hands until the round is over
            hand_finished = False
            first_move, hand_type, discard_type = self.players[self.leading_player].play_first_move()
            last_move = first_move
            last_player = current_player
            current_player = (current_player + 1) % 3
            while not hand_finished: 
                print(last_player, current_player)
                if last_player == current_player: 
                    # everyone passed
                    print(self.players[current_player].name, ' won this round')
                    hand_finished = True
                    self.leading_player = last_player
                    if len(self.players[current_player].cards) == 0:
                        round_finished = True
                        print(self.players[current_player].name, ' WON THE GAME')
                else:
                    move = self.players[current_player].play(last_move, hand_type, discard_type)
                    if move:
                        last_move = move 
                        last_player = current_player
                    
                    current_player = (current_player + 1) % 3
            # only play one hand
            break 
                

    def run_bidding(self):
        # each player makes a bid
        top_bid = 0
        top_bidder = None
        for i in range(3):
            player = (self.leading_player + i) % 3
            current_bid = self.players[player].get_bid(top_bid)
            if current_bid > top_bid:
                top_bidder = player
                top_bid = current_bid
            if top_bid == 3:
                break
        
        print(self.players[top_bidder].name, ' starts and bid', top_bid)
        return top_bidder



