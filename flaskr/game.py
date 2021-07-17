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

from .model.game import Game
from .model.player import Player

from .model.utils import validate_type, validate_discard

N_PLAYERS = 1

bp = Blueprint('game', __name__, url_prefix='/')

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    print('happening')
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
                    record = {'game_id': game_id, 
                              'players': [
                                  {
                                      'user_id': session['_user_id'], 
                                      'username': current_user.username
                                  }
                                  ],
                              'n_players': 1
                              }
                    db.games.insert_one(record)
                    break
            
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            game = get_game(game_id)
            if game is None:
                error = "No game exists with that code"
            elif session['_user_id'] in [x['user_id'] for x in game['players']]:
                print('player re-entering room')
            elif game['n_players'] == 3:
                error = "Game is full"
            else:
                game['players'].append({
                    'user_id': session['_user_id'], 
                    'username': current_user.username})
                game['n_players'] += 1
                print('adding player to game', game)
                update_game(game)

        ## TODO add a leave room option 

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')

@bp.route('/<id>', methods=('GET', 'POST'))
def gameboard(id):
    db = get_db().ddz
    game = db.games.find_one({'game_id': id})
    return render_template('game/game.html', game=game)

@socketio.on('connect')
def connectionMade():
    print('Connection occured! with ', current_user.username, request.sid)

@socketio.on('add to database')
def add_to_db(data):
    game = get_game(data['game_id'])
    for player in game['players']:
        if player['username'] == data['username']:
            print('added ', player['username'], 'socket id', request.sid)
            player['socketid'] = request.sid
    update_game(game)

@socketio.on('debug')
def debug(data):
    """For random functions I want to test out, so that I can activate them on click"""
    run_game(data['game_id'])
    #  update_game(get_game(data['game_id']))

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', current_user.username)

@socketio.on('remove from database')
def removeFromDB(data):
    print("Not implemented yet")

def run_game(game_id):
    print('running a game')
    initialize_game(game_id)
    get_bid(game_id)

def initialize_game(game_id):
    print('dealing cards and initializing game')
    game = get_game(game_id)

    deck = [16, 17] # deck starts with two jokers
    for i in range(4): 
        deck += list(range(3, 16))

    random.shuffle(deck)

    hands = [sorted(deck[:17]), sorted(deck[17:34]), sorted(deck[34:51])]
    game['blind'] = sorted(deck[51:])
    
    first_bid = random.randint(0, 3)
    first_bid = 0 # TEMPORARY for testing with one player
    flipped_card = random.choice(hands[first_bid])
    game['flipped_card'] = flipped_card

    for h, p in zip(hands, game['players']):
        p['hand'] = h
        p['visible_cards'] = []

    game['players'][first_bid]['visible_cards'].append(flipped_card)

    # Determine who starts the bidding (who has the flipped card)
    game['first_bidder'] = first_bid
    game['current_player'] = first_bid

    game['current_player'] = 0 # TEMPORARY for testing with one player
    update_game(game)

def get_bid(game_id):
    print('starting bidding')
    game = get_game(game_id)
    p = game['players'][game['current_player']] # first bid
    print('Sending bid request to ', p['username'], p['socketid'])
    socketio.emit('bid', to=p['socketid'])


def get_game(game_id):
    return get_db().ddz.games.find_one({'game_id': game_id})

def update_game(game):
    """Send new game state to all players and update game DB record"""
    for p in game['players']:
        socketio.emit('update gameboard', generate_game_data(game, p))
    return get_db().ddz.games.replace_one({'game_id': game['game_id']}, game)

def generate_game_data(game, player):
    """Create a dict to send to the client that includes relevant data"""
    game_state = {
        'usernames': [p['username'] for p in game['players']],
        'other_players': [], 
        'hand_type': game.get('hand_type', 'None'),
        'hand_history': game.get('hand_history', [])
    }

    for p in game['players']:
        if p['user_id'] == player['user_id']:
            game_state['hand'] = p.get('hand', [])
        else:
            game_state['others'].append({
                'n_cards': len(p.get('hand', [])),
                'visible_cards': []
                })
    return game_state

@socketio.on("submit bid")
def add_bid(data):
    print('received a bid', data)
    game = get_game(data['info']['game_id'])
    p = game['players'][game['current_player']] # first bid
    p['bid'] = int(data['bid'])
    flash_message(f'{p["username"]} bidded {p["bid"]}')
    for p in game['players']:
        if 'bid' not in p:
            game['current_player'] = (game['current_player'] + 1) % N_PLAYERS
            update_game(game)
            get_bid(game['game_id'])
            return

    # bidding is complete, find winner and start game 
    assign_landlord(game)

def assign_landlord(game):
    """Takes a game_id and assigns a landlord based on bids"""
    winner, winner_loc = None, None
    current_high_bid = 0
    for i, p in enumerate(game['players']):
        if p['bid'] > current_high_bid:
            current_high_bid = p['bid']
            winner = p
            winner_loc = i
    
    flash_message(f'Bidding complete! The landlord is {p["username"]}')
    game['current_player'] = winner_loc
    p['hand'] += game['blind']
    p['visible_cards'] += game['blind']
    game['landlord'] = p
    update_game(game)
    time.sleep(2)
    get_move(game['game_id'])


def get_move(game_id):
    game = get_game(game_id)
    p = game['players'][game['current_player']] # it's this person's move
    print('Sending move request to ', p['username'], p['socketid'])
    socketio.emit('make move', to=p['socketid'])

def flash_message(message: str) -> None:
    """Displays a notification in red at the top of the client"""
    socketio.emit('flash', message)

@socketio.on("submit move")
def add_move(data):
    print('received a move', data)
    game = get_game(data['info']['game_id'])
    p = game['players'][game['current_player']]

    if data['move'] == '':
        move = []
    else:
        move = [int(x) for x in data['move'].split(',')]

    if data['discard'] == '':
        discard = []
    else:
        discard = [int(x) for x in data['discard'].split(',')]
    
    valid_move, valid_discard = validate_move(game, move, discard)
    if not valid_move and not valid_discard: 
        # redo, get the same move
        get_move(game['game_id'])
    else:
        game['hand_type'] = valid_move
        game['discard_type'] = valid_discard
        flash_message(
            f'{p["username"]} played a {valid_move} with {valid_discard}')
        for card in [*move, *discard]:
            p['hand'].remove(card)
        
        # check if the player has won 
        if len(p['hand']) == 0:
            print('game is over')
            return 
        else:
            # move onto the next player
            game['current_player'] = (game['current_player'] + 1) % N_PLAYERS
            update_game(game)
            time.sleep(2)
            get_move(game['game_id'])


def validate_move(game, move, discard):
    """Takes in a game, attempted move, and attempted discard 
    and returns whether they are valid"""
    hand_type = validate_type(move)
    discard_type = validate_discard(discard, hand_type)
    if 'hand_type' in game:
        # there is already a round type, make sure it's valid
        return game['hand_type'] == hand_type, game['discard_type'] == discard_type
    elif hand_type and discard_type:
        # set the first move
        return hand_type, discard_type
    else:
        # first move was invlaid
        return False, False