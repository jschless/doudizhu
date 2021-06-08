from .player import Player
from .round import Round

class Game:
    game_id: str
    player1: Player
    player2: Player
    player3: Player
    scores: dict 
    round: Round

    def __init__(self, game_id):
        self.game_id = game_id
        self.player1 = None
        self.player2 = None
        self.player3 = None

    def __dict__(self):
        return {
            'game_id': self.game_id,
            'player1': {} if self.player1 is None else dict(self.player1),
            'player2': {} if self.player2 is None else dict(self.player2),
            'player3': {} if self.player3 is None else dict(self.player3),
        }

    def add_player(self, player):
        if self.player1 is None:
            self.player1 = player
        elif self.player2 is None:
            self.player2 = player
        elif self.player3 is None:
            self.player3 = player
        else:
            raise RuntimeError("Game is full!")

    def start_game(self):
        players = [self.player1, self.player2, self.player3]
        if all(players):
            # all players have joined
            self.round = Round(players)
            self.round.start_round()
    

    