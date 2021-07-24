import random
import string

from flaskr.db import get_db
from flaskr.socket_utils import send_socket, flash_message
from flaskr.utils import validate_type, validate_discard
from flaskr.user import User


class Game:
    def __init__(self, game_id):
        """Creates a game given a game_id (MongoDB record)"""
        record = get_db().ddz.games.find_one({'game_id': game_id})
        print(record)
        if record is None:
            print('record not found with game_id', game_id)
            raise KeyError

        for key, value in record.items():
            setattr(self, key, value)

        default_vars = [('hand_type', None), ('discard_type', None),
                        ('hand_history', [])]
        for var_name, default_value in default_vars:
            if not hasattr(self, var_name):
                setattr(self, var_name, default_value)

    @classmethod
    def create_game(cls):
        """Creates a game"""
        db = get_db().ddz
        while True:
            game_id = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=5))
            if db.games.find_one({'game_id': game_id}) is None:
                # no existing game has this key
                record = {'game_id': game_id, 'players': [], 'scoreboard': {}}
                db.games.insert_one(record)
                break

        return cls(game_id)

    def add_player_to_db(self, user: User, session, request):
        self.players = [
            p for p in self.players if p['username'] != user.username]

        self.players.append({
            'user_id': session['_user_id'],
            'username': user.username,
            'socketid': request.sid
        })

        user.join_game(self.game_id)
        self.update()

    def remove_player_from_db(self, user: User):
        """On disconnect, we remove the player from the database"""
        self.players = [
            p for p in self.players if p['username'] != user.username]
        user.leave_game()
        self.update()

    def update(self):
        """Updates the MongoDB record and sends a new gamestate to all connected users"""
        for p in self.players:
            send_socket('update gameboard',
                        self.generate_game_data(p), p['socketid'])
        return get_db().ddz.games.replace_one({'game_id': self.game_id}, self.__dict__)

    def generate_game_data(self, player):
        """Create a dict to send to the client that includes relevant data"""
        game_state = {
            'other_players': [],
            'hand_type': self.hand_type,
            'discard_type': self.discard_type,
            'hand_history': self.hand_history,
            'scoreboard': self.scoreboard
        }

        usernames = []
        for p in self.players:
            if hasattr(self, 'landlord'):
                if p['username'] == self.landlord:
                    usernames.append(p['username'] + ' (landlord)')
                else:
                    usernames.append(p['username'] + ' (peasant)')
            else:
                usernames.append(p['username'])
            if p['user_id'] == player['user_id']:
                game_state['hand'] = p.get('hand', [])
            else:
                game_state['other_players'].append({
                    'username': p['username'],
                    'n_cards': len(p.get('hand', [])),
                    'visible_cards': p.get('visible_cards', [])
                })

            game_state['usernames'] = usernames
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
            p['hand'] = h
            p['visible_cards'] = []

        # flip over the card of the first player
        self.players[first_bid]['visible_cards'].append(flipped_card)

        # Determine who starts the bidding (who has the flipped card)
        self.first_bidder = first_bid
        self.current_player = first_bid

        # wipe round variables
        self.hand_type = None
        self.discard_type = None
        self.hand_history = []

        # reset player level variables
        for key in ['bid']:
            for p in self.players:
                if key in p:
                    del p[key]

        self.update()
        self.get_bid(minimum=-1)

    # Bidding Section

    def get_bid(self, minimum: int, first_bid: bool = False):
        """Requests a bid from the next player who needs to bid"""
        p = self.players[self.current_player]
        # print('Sending bid request to ', p['username'], p['socketid'])
        if first_bid:
            flash_message(f'{p["username"]} is now bidding')
        send_socket('bid', minimum, p['socketid'])

    def register_bid(self, data):
        p = self.players[self.current_player]
        p['bid'] = int(data['bid'])
        max_bid = max(p.get('bid', 0) for p in self.players)
        self.update()
        if p['bid'] == 3 or all('bid' in p for p in self.players):
            # bidding is complete, find winner and start game
            self.assign_landlord()
        else:
            self.advance_player()
            flash_message(f'''{p["username"]} bid {p["bid"]}, 
                {self.players[self.current_player]["username"]} is now bidding''')
            self.update()
            self.get_bid()

    def assign_landlord(self):
        """Determines who the landlord is"""
        winner_loc, winner = max(enumerate(self.players),
                                 key=lambda x: x[1].get('bid', 0))

        if winner['bid'] == 0:
            raise ValueError("Everyone passed, you should reshuffle")

        flash_message(
            f'Bidding complete! The landlord is {winner["username"]}')
        self.current_player = winner_loc
        self.winning_bid = winner['bid']

        winner['hand'] += self.blind
        winner['hand'] = sorted(winner['hand'])
        winner['visible_cards'] += self.blind
        self.landlord = winner['username']
        self.update()
        self.get_move()

    # MOVING SECTION

    def get_move(self, retry=False):
        p = self.players[self.current_player]
        if retry:
            flash_message('Invalid move attempt, try again', player=p)
        send_socket('make move', None, p['socketid'])

    def register_move(self, data):
        p = self.players[self.current_player]
        move = [int(x) for x in data['move']]
        discard = [int(x) for x in data['discard']]

        try:
            valid_move, valid_discard = self.validate_move(move, discard)
        except Exception as e:
            # redo, get the same move
            self.get_move(retry=True)
        else:
            self.hand_type = valid_move
            self.discard_type = valid_discard
            if len(move) == 0:
                flash_message(f'{p["username"]} passed')
            else:
                self.hand_history.append((move, discard, self.current_player))
                flash_message(
                    f'{p["username"]} played a {valid_move} with {valid_discard}')

                for card in [*move, *discard]:
                    p['hand'].remove(card)
                    if card in p['visible_cards']:
                        p['visible_cards'].remove(card)

                if ((valid_move == "quad" and valid_discard == "no-discard")
                        or (valid_move == "rocket")):
                    # double the bid on a bomb
                    self.winning_bid = 2*self.winning_bid

            # move onto the next move
            self.update()
            self.determine_next_move(p)

    def determine_next_move(self, p):
        # check if the player has just won
        if len(p['hand']) == 0:
            flash_message(f'Round is over, {p["username"]} won',
                          event='flash append')
            self.update_scoreboard(p)
            return
        else:
            # move onto the next player
            self.advance_player()
            if self.hand_history[-1][2] == self.current_player:
                # the last move was by the current player
                winner = self.players[self.current_player]
                flash_message(f'{winner["username"]} won that hand')
                self.reset_hand_data()
                self.update()
                send_socket('hand over', None, winner['socketid'])
            else:
                flash_message(
                    f'waiting on {self.players[self.current_player]["username"]} to move',
                    event='flash append')
                self.update()
                self.get_move()

    def validate_move(self, move, discard):
        """Takes in an attempted move and attempted discard and returns whether they are valid"""
        print('validating', move, discard)
        if len(move) == 0 and len(discard) == 0:  # PASS
            if self.hand_type:
                return self.hand_type, self.discard_type
            else:
                raise Exception("attempted to pass on the first move")

        hand_type = validate_type(move)
        discard_type = validate_discard(discard, hand_type)

        if self.hand_type is not None:
            # there is already a round type, make sure it's valid
            if self.hand_type == hand_type and self.discard_type == discard_type:
                last_move = self.hand_history[-1]
                if sum(last_move[0]) >= sum(move):
                    raise RuntimeError(
                        f'Attempted move is weaker than last hand')
                else:
                    return hand_type, discard_type
            elif hand_type == "quad" and discard_type == "no-discard":
                return "quad", "no-discard"
            elif hand_type == "rocket" and discard_type == "no-discard":
                return "rocket", "no-discard"
            else:
                raise RuntimeError(
                    f'''Hand type and discard type did not match what was required
                    ({hand_type} !=  {self.hand_type} 
                    or {discard_type} != {self.discard_type}''')
        elif hand_type and discard_type:
            # both are valid, set the first move
            return hand_type, discard_type
        else:
            # first move was invalid
            raise RuntimeError(
                f'''Attempted move was invalid move: {move} discard: {discard}''')

    def advance_player(self):
        """Advances current player variable to the next player"""
        self.current_player = (self.current_player + 1) % 3

    def reset_hand_data(self):
        self.hand_type = None
        self.discard_type = None
        self.hand_history = []

    def update_scoreboard(self, winning_player):
        """Updates the scores after the round is over"""
        bid = self.winning_bid
        landlord_won = 1 if winning_player['username'] == self.landlord else -1
        for p in self.players:
            u = p['username']
            if u == self.landlord:
                self.scoreboard[u] = self.scoreboard.get(
                    u, 0) + 2*bid*landlord_won
            else:
                self.scoreboard[u] = self.scoreboard.get(
                    u, 0) - bid*landlord_won
        self.update()
        self.initialize_round()