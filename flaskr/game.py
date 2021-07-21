import functools
import random
import time
import string
from pprint import pprint

from flask_login.utils import login_required

from . import socketio

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import current_user, login_required
from flask_socketio import emit
from flaskr.db import get_db

from .utils import validate_type, validate_discard

N_PLAYERS = 3 # can be set to one to test game with just one client

bp = Blueprint('game', __name__, url_prefix='/')

@bp.route('', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        error = None
        game = None
        db = get_db().ddz
        if 'create' in request.form:
            game_id = None
            while True:
                game_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                if db.games.find_one({'game_id': game_id}) is None:
                    # no existing game has this key
                    record = {'game_id': game_id, 'players': [], 'scoreboard': {}}
                    db.games.insert_one(record)
                    break            
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            game = get_game(game_id)
            if game is None:
                error = "No game exists with that code"
            elif session['_user_id'] in [x['user_id'] for x in game['players']]:
                print('player re-entering room')
            elif len(game['players']) == 3:
                error = "Game is full"
            else:
                # add player to game on connection
                print('player has successfully joined')

        ## TODO add a leave room option 

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')

@login_required
@bp.route('/<id>', methods=('GET', 'POST'))
def gameboard(id):
    game = get_game(id)
    return render_template('game/game.html', game=game)

@socketio.on('connect')
def connectionMade():
    print('Connection occured! with type ', type(current_user), current_user.username, request.sid)


@socketio.on('add to database')
def add_to_db(data):
    game = get_game(data['game_id'])

    game['players'] = [p for p in game['players'] if p['username'] != current_user.username]

    game['players'].append({
        'user_id': session['_user_id'], 
        'username': current_user.username,
        'socketid': request.sid
    })

    update_game(game)

@socketio.on('debug')
def debug(data):
    """For random functions I want to test out, so that I can activate them on click"""
    run_round(data['game_id'])
    #update_game(get_game(data['game_id']))

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', current_user) 

@socketio.on('next round')
def run_round(game_id):
    print('running a round')
    initialize_game(game_id)
    get_bid(game_id, 0, first_bid=True)


def initialize_game(game_id):
    print('dealing cards and initializing game')
    game = get_game(game_id)

    deck = [16, 17] # deck starts with two jokers
    for i in range(4): 
        deck += list(range(3, 16))

    random.shuffle(deck)

    hands = [sorted(deck[:17]), sorted(deck[17:34]), sorted(deck[34:51])]
    game['blind'] = sorted(deck[51:])
    
    first_bid = random.randint(0, 2)
    print('first bid goes to', first_bid)
    # first_bid = 0 # TEMPORARY for testing with one player
    flipped_card = random.choice(hands[first_bid])
    game['flipped_card'] = flipped_card

    for h, p in zip(hands, game['players']):
        p['hand'] = h
        p['visible_cards'] = []

    game['players'][first_bid]['visible_cards'].append(flipped_card)

    # Determine who starts the bidding (who has the flipped card)
    game['first_bidder'] = first_bid
    game['current_player'] = first_bid

    for key in ['hand_type', 'discard_type', 'landlord']:
        if key in game:
            del game[key]

    # player level variables
    for key in ['bid']:
        for p in game['players']:
            if key in p:
                del p[key]

    game['hand_history'] = []

    update_game(game)

def get_bid(game_id, minimum: int, first_bid: bool = False):
    game = get_game(game_id)
    p = game['players'][game['current_player']]
    print('Sending bid request to ', p['username'], p['socketid'])
    if first_bid:
        flash_message(f'{p["username"]} is now bidding')
    socketio.emit('bid', minimum, to=p['socketid'])


def get_game(game_id):
    return get_db().ddz.games.find_one({'game_id': game_id})

def update_game(game):
    """Send new game state to all players and update game DB record"""
    # pprint(game)
    for p in game['players']:
        socketio.emit('update gameboard', generate_game_data(game, p),
         to=p['socketid'])
    return get_db().ddz.games.replace_one({'game_id': game['game_id']}, game)

def generate_game_data(game, player):
    """Create a dict to send to the client that includes relevant data"""
    game_state = {
        'other_players': [], 
        'hand_type': game.get('hand_type', 'None'),
        'discard_type': game.get('discard_type', 'None'),
        'hand_history': game.get('hand_history', []),
        'scoreboard': game.get('scoreboard', {})
    }

    usernames = []
    for p in game['players']:
        if 'landlord' in game:
            if p['username'] == game['landlord']:
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

@socketio.on("submit bid")
def add_bid(data):
    print('received a bid', data)
    game = get_game(data['info']['game_id'])
    p = game['players'][game['current_player']] # first bid
    p['bid'] = int(data['bid'])
    max_bid = max(p.get('bid', 0) for p in game['players'])
    update_game(game)
    if p['bid'] == 3 or all('bid' in p for p in game['players']):
        # bidding is complete, find winner and start game 
        assign_landlord(game)
    else:
        game['current_player'] = (game['current_player'] + 1) % N_PLAYERS
        flash_message(f'''{p["username"]} bid {p["bid"]}, 
            {game['players'][game["current_player"]]["username"]} is now bidding''')
        update_game(game)
        get_bid(game['game_id'], max_bid, first_bid=False)

    
def assign_landlord(game):
    """Takes a game_id and assigns a landlord based on bids"""
    winner, winner_loc = None, None
    current_high_bid = 0
    for i, p in enumerate(game['players']):
        if p.get('bid', 0) > current_high_bid:
            current_high_bid = p['bid']
            winner = p
            winner_loc = i
    
    flash_message(f'Bidding complete! The landlord is {winner["username"]}')
    game['current_player'] = winner_loc
    game['winning_bid'] = current_high_bid
    winner['hand'] += game['blind']
    winner['hand'] = sorted(winner['hand'])
    winner['visible_cards'] += game['blind']
    game['landlord'] = winner['username']
    update_game(game)
    get_move(game['game_id'])

@socketio.on("next hand")
def get_move(game_id, retry=False):
    game = get_game(game_id)
    p = game['players'][game['current_player']] # it's this person's move
    print('Sending move request to ', p['username'], p['socketid'])
    if retry:
        flash_message('Invalid move attempt, try again', player=p)
        socketio.emit('make move', to=p['socketid'])

    socketio.emit('make move', to=p['socketid'])
    

def flash_message(message: str, player=None, event='flash') -> None:
    """Displays a notification in red at the top of the client
    
    event: "flash" -> rewrite to flash, "flash append" -> append toflash
    player: pass players dict if you want to flash to a specific user
    """
    if player:
        socketio.emit(event, message, to=player['socketid'])
    else:
        socketio.emit(event, message)

@socketio.on("submit move")
def add_move(data):
    print('received a move', data)
    game = get_game(data['info']['game_id'])
    p = game['players'][game['current_player']]

    move = [int(x) for x in data['move']]

    discard = [int(x) for x in data['discard']]
    
    try:
        valid_move, valid_discard = validate_move(game, move, discard)
    except Exception as e:
        # redo, get the same move
        print(e, game)
        get_move(game['game_id'], retry=True)
    else:
        game['hand_type'] = valid_move
        game['discard_type'] = valid_discard
        if len(move) == 0:
            flash_message(
                f'{p["username"]} passed')
        else:
            game['hand_history'].append((move, discard, game['current_player']))
            flash_message(
                f'{p["username"]} played a {valid_move} with {valid_discard}')

        for card in [*move, *discard]:
            p['hand'].remove(card)
            if card in p['visible_cards']:
                p['visible_cards'].remove(card)
        
        if ((valid_move == "quad" and valid_discard == "no-discard") 
            or (valid_move == "rocket")):
            # double the bid on a bomb
            game['winning_bid'] = 2*game['winning_bid']

        # check if the player has just won 
        if len(p['hand']) == 0:
            flash_message(f'Round is over, {p["username"]} won', 
                event='flash append')
            update_scoreboard(game, p)
            return 
        else:
            # move onto the next player
            game['current_player'] = (game['current_player'] + 1) % N_PLAYERS
            if game['hand_history'][-1][2] == game['current_player']:
                # the last move was by the current player
                winner = game["players"][game["current_player"]]
                flash_message(f'{winner["username"]} won that hand')
                del game['hand_type'] 
                del game['discard_type'] 
                game['hand_history'] = []
                update_game(game)
                socketio.emit('hand over', to=winner['socketid'])
            else:
                flash_message(f'waiting on {game["players"][game["current_player"]]["username"]} to move', 
                    event='flash append')
                update_game(game)
                get_move(game['game_id'])


def update_scoreboard(game: dict, winning_player: dict):
    """Updates the scores after the round is over"""
    bid = game['winning_bid'] 
    landlord_won = 1 if winning_player['username'] == game['landlord'] else -1
    for p in game['players']:
        u = p['username']
        if u == game['landlord']:
            game['scoreboard'][u] = game['scoreboard'].get(u, 0) + 2*bid*landlord_won
        else:
            game['scoreboard'][u] = game['scoreboard'].get(u, 0) - bid*landlord_won
    print('game at end of round')
    pprint(game)
    update_game(game)
    run_round(game['game_id'])
    

def validate_move(game, move, discard):
    """Takes in a game, attempted move, and attempted discard 
    and returns whether they are valid"""
    print('validating', move, discard)
    if len(move) == 0 and len(discard) == 0:
        # PASS 
        if 'hand_type' in game:
            return game['hand_type'], game['discard_type']
        else:
            raise Exception("attempted to pass on the first move")

    hand_type = validate_type(move)
    discard_type = validate_discard(discard, hand_type)

    if 'hand_type' in game:
        # there is already a round type, make sure it's valid
        if game['hand_type'] == hand_type and game['discard_type'] == discard_type:
            last_move = game['hand_history'][-1]
            if sum(last_move[0]) >= sum(move):
                raise RuntimeError(f'Attempted move is weaker than last hand')
            else:
                return hand_type, discard_type
        elif hand_type == "quad" and discard_type == "no-discard":
            return "quad", "no-discard"
        elif hand_type == "rocket" and discard_type == "no-discard":
            return "rocket", "no-discard"
        else:
            raise RuntimeError(f'''Hand type and discard type did not match what was required
             ({hand_type} !=  {game["hand_type"]} or {discard_type} != {game["discard_type"]}''')
    elif hand_type and discard_type:
        # set the first move
        return hand_type, discard_type
    else:
        # first move was invalid
        raise RuntimeError(f'Attempted move was invalid move: {move} discard: {discard}')