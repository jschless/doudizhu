from dataclasses import asdict
import random
import string
from doudizhu.db import get_db
from doudizhu.socket_utils import send_socket, flash_message
from doudizhu.user import User
from doudizhu.hand_types import (
    hand_type_from_dict,
    validate_move,
    UninitializedType,
    Empty,
    HandType,
)


class Game:
    def __init__(self, game_id):
        """Creates a game given a game_id (MongoDB record)"""
        record = get_db().ddz.games.find_one({"game_id": game_id})
        if record is None:
            print("record not found with game_id", game_id)
            raise KeyError

        for key, value in record.items():
            if key in ["landlord", "game_owner"]:
                setattr(self, key, User.from_record(value))
            elif key in ["hand_type", "discard_type"]:
                setattr(self, key, hand_type_from_dict(value))
            else:
                setattr(self, key, value)

        self.players = []
        for p in record["players"]:
            self.players.append(User.from_record(p))

        default_vars = [
            ("hand_type", UninitializedType()),
            ("discard_type", UninitializedType()),
            ("hand_history", []),
            ("winning_bid", None),
            ("round_in_progress", False),
        ]
        for var_name, default_value in default_vars:
            if not hasattr(self, var_name):
                setattr(self, var_name, default_value)

    def to_mongo(self):
        mongo_record = {}
        for k, v in self.__dict__.items():
            if k == "players":
                mongo_record[k] = [p.asdict() for p in v]
            elif k in ["landlord", "game_owner"]:
                mongo_record[k] = v.asdict()
            elif k in ["hand_type", "discard_type"]:
                mongo_record[k] = asdict(v)
            else:
                mongo_record[k] = v
        return mongo_record

    @classmethod
    def create_game(cls):
        """Creates a game"""
        db = get_db().ddz
        while True:
            game_id = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=5)
            )
            if db.games.find_one({"game_id": game_id}) is None:
                # no existing game has this key
                record = {"game_id": game_id, "players": [], "scoreboard": {}}
                db.games.insert_one(record)
                break

        return cls(game_id)

    def add_player_to_game(self, user: User):
        if len(self.players) == 0:
            self.game_owner = user

        if user not in self.players:
            user.join_game(self.game_id)
            self.players.append(user)
        else:
            loc = self.players.index(user)
            self.players[loc] = user
        self.update()

    def remove_player_from_game(self, user: User):
        """On disconnect, we remove the player from the database"""
        self.players = [p for p in self.players if p != user]
        user.leave_game()
        self.update()

    def update(self, game_over: bool = False):
        """Updates the MongoDB record

        and sends a new gamestate to all connected users"""
        for p in self.players:
            send_socket(
                "update gameboard", self.generate_game_data(p, game_over), p.sid
            )
        return get_db().ddz.games.replace_one(
            {"game_id": self.game_id}, self.to_mongo()
        )

    def generate_game_data(self, player: User, game_over: bool = False):
        """Create a dict to send to the client that includes relevant data"""
        game_state = {
            "other_players": [],
            "game_id": self.game_id,
            "winning_bid": self.winning_bid,
            "hand_type": self.hand_type.name,
            "discard_type": self.discard_type.name,
            "hand_history": self.hand_history,
            "scoreboard": self.scoreboard,
        }

        if len(self.scoreboard) == 3:
            usernames = [
                tup[0] for tup in sorted(self.scoreboard.items(), key=lambda p: -p[1])
            ]
        else:
            usernames = [p.username for p in self.players]

        for p in self.players:
            if p == player:
                game_state["hand"] = p.hand
                game_state["last_move"] = p.last_move
                game_state["last_discard"] = p.last_discard
            else:
                game_state["other_players"].append(
                    {
                        "username": p.username,
                        "n_cards": len(p.hand),
                        "visible_cards": p.visible_cards if not game_over else p.hand,
                        "last_move": p.last_move,
                        "last_discard": p.last_discard,
                    }
                )

        game_state["usernames"] = usernames

        # logic for beginning the game
        if (
            player == self.game_owner
            and len(self.players) == 3
            and not self.round_in_progress
        ):
            game_state["start_game"] = True
        else:
            game_state["start_game"] = False

        return game_state

    def initialize_round(self):
        deck = [16, 17]  # deck starts with two jokers
        for i in range(4):
            deck += list(range(3, 16))

        random.shuffle(deck)

        hands = [sorted(deck[:17]), sorted(deck[17:34]), sorted(deck[34:51])]
        self.blind = sorted(deck[51:])

        first_bid = random.randint(0, 2)
        flipped_card = random.choice(hands[first_bid])
        self.flipped_card = flipped_card

        for h, p in zip(hands, self.players):
            p.hand = h
            p.visible_cards = []

        # flip over the card of the first player
        self.players[first_bid].visible_cards.append(flipped_card)

        # Determine who starts the bidding (who has the flipped card)
        self.first_bidder = first_bid
        self.current_player = first_bid

        # wipe round variables
        self.reset_hand_data()

        self.round_in_progress = True
        self.update()
        self.get_bid(minimum=-1)

    # Bidding Section

    def get_bid(self, minimum: int, first_bid: bool = False):
        """Requests a bid from the next player who needs to bid"""
        p = self.players[self.current_player]
        if first_bid:
            flash_message(f"{p.username} is now bidding", address=self.game_id)
        send_socket("bid", minimum, p.sid)

    def register_bid(self, data):
        p = self.players[self.current_player]
        p.bid = int(data["bid"])
        max_bid = max(p.bid for p in self.players if p.bid is not None)
        self.update()
        if p.bid == 3 or all(p.bid is not None for p in self.players):
            # bidding is complete, find winner and start game
            self.assign_landlord()
        else:
            self.advance_player()
            flash_message(
                f"""{p.username} bid {p.bid},
                {self.players[self.current_player].username} is now bidding""",
                address=self.game_id,
            )
            self.update()
            self.get_bid(minimum=max_bid)

    def assign_landlord(self):
        """Determines who the landlord is"""
        winner_loc, winner = max(
            enumerate(self.players),
            key=lambda x: x[1].bid if x[1].bid is not None else 0,
        )

        if winner.bid == 0:
            flash_message("Everyone passed, reshuffling")
            self.round_in_progress = False
            self.initialize_round()
            return

        flash_message(
            f"Bidding complete! The landlord is {str(winner)}", address=self.game_id
        )
        self.current_player = winner_loc
        self.winning_bid = winner.bid

        winner.hand = sorted(winner.hand + self.blind)
        winner.visible_cards += self.blind
        self.landlord = winner
        self.update()
        self.get_move()

    # MOVING SECTION

    def get_move(self, retry=False):
        p = self.players[self.current_player]
        if retry:
            flash_message("Invalid move attempt, try again", address=p.sid)
        send_socket("make move", None, p.sid)

    def register_move(self, data):
        p = self.players[self.current_player]
        move = [int(x) for x in data["move"]]
        discard = [int(x) for x in data["discard"]]

        try:
            move_type, discard_type = validate_move(
                move, discard, self.hand_type, self.discard_type
            )
        except RuntimeError as e:
            print(e, "Move was invalid", move, discard)
            self.get_move(retry=True)
        else:
            if self.hand_type == UninitializedType():
                self.hand_type = move_type
                self.discard_type = discard_type

            msg = f"{str(p)} passed"
            if move_type != Empty():
                self.hand_history.append((move, discard, self.current_player))
                msg = f"{str(p)} played a {move_type} with {discard_type}"
            flash_message(msg, address=self.game_id)

            p.last_move = move
            p.last_discard = discard
            for card in [*move, *discard]:
                p.hand.remove(card)
                if card in p.visible_cards:
                    p.visible_cards.remove(card)

            if move_type.name in ["2-triple straight", "3-triple straight"]:
                send_socket("airplane", {})
            elif (
                move_type.name == "quad" and discard_type == Empty()
            ) or move_type.name == "Rocket":
                self.bomb(move_type)
            elif move == [3, 4, 5, 6, 7]:
                send_socket("baby-straight", {})

            # move onto the next move
            self.update()
            self.determine_next_move(p)

    def bomb(self, move_type: HandType):
        self.winning_bid = 2 * self.winning_bid
        self.hand_type = move_type
        self.discard_type = Empty()
        kind = "bomb" if move_type.name == "quad" else "rocket"
        send_socket(kind, {})

    def game_over(self, p: User):
        """Handles things for when a game has ended"""
        flash_message(
            f"""Round is over, {str(p)} won...
            {str(self.game_owner)} may start another round when ready""",
            event="flash append",
            address=self.game_id,
        )
        self.round_in_progress = False
        self.update_scoreboard(p)
        self.update(game_over=True)

    def determine_next_move(self, p):
        # check if the player has just won
        if len(p.hand) == 0:
            return self.game_over(p)

        # move onto the next player
        self.advance_player()
        if self.hand_history[-1][2] == self.current_player:
            # the last move was by the current player
            winner = self.players[self.current_player]
            flash_message(f"{str(winner)} won that hand", address=self.game_id)
            self.reset_hand_data()
            self.update()
            send_socket("hand over", None, winner.sid)
        else:
            flash_message(
                f"waiting on {str(self.players[self.current_player])} to move",
                event="flash append",
                address=self.game_id,
            )
            self.update()
            self.get_move()

    def advance_player(self):
        """Advances current player variable to the next player"""
        self.current_player = (self.current_player + 1) % 3

    def reset_hand_data(self):
        self.hand_type = UninitializedType()
        self.discard_type = UninitializedType()
        self.hand_history = []
        self.last_move = []
        for p in self.players:
            p.bid = None
            p.last_move = []
            p.last_discard = []
            p.update_db()

    def update_scoreboard(self, winning_player: User):
        """Updates the scores after the round is over"""
        bid = self.winning_bid
        landlord_won = 1 if winning_player == self.landlord else -1
        for p in self.players:
            u = p.username
            if p == self.landlord:
                self.scoreboard[u] = self.scoreboard.get(u, 0) + 2 * bid * landlord_won
                p.update_scoreboard(2 * bid * landlord_won)
            else:
                self.scoreboard[u] = self.scoreboard.get(u, 0) - bid * landlord_won
                p.update_scoreboard(-bid * landlord_won)

    def initialize_test_round(self):
        """Creates a test round with loaded hands to test out joker bombs, airplanes,"""
        hands = [
            [3, 3, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15],
            [4, 4, 4, 5, 5, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17],
            [6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14],
        ]
        self.blind = [14, 15, 15]

        first_bid = 1
        self.flipped_card = 4

        for h, p in zip(hands, self.players):
            p.hand = h
            p.visible_cards = []

        self.players[first_bid].visible_cards.append(self.flipped_card)

        # Determine who starts the bidding (who has the flipped card)
        self.first_bidder = first_bid
        self.current_player = first_bid

        # wipe round variables
        self.reset_hand_data()

        self.round_in_progress = True
        self.update()
        self.get_bid(minimum=-1)
