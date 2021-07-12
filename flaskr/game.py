import functools
import random
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

bp = Blueprint('game', __name__, url_prefix='/game')

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
                    print('creating game with id', game_id)
                    print(session)
                    gameboard = initialize_game()
                    record = {'game_id': game_id, 
                              'players': [(session['_user_id'], current_user.username)],
                              'n_players': 1,
                              **gameboard
                              }
                    # player = Player(session['username'], session['user_id'])
                    # game = Game(player, game_id)
                    db.games.insert_one(record)
                    break
            
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            game = db.games.find_one({'game_id': game_id})
            if game['n_players'] == 3:
                initialize_game()
            if game is None:
                error = "No game exists with that code"
            elif session['_user_id'] in [x[0] for x in game['players']]:
                print('player re-entering room')
            elif game['n_players'] == 3:
                error = "Game is full"
            else:
                game['players'].append((session['_user_id'], current_user.username))
                game['n_players'] += 1
                print('adding player to game', game)
                db.games.replace_one({'game_id': game_id}, game)
                if game['n_players'] == 3:
                    initialize_game()


        ## TODO add a leave room option 

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')

@bp.route('/<id>', methods=('GET',))
def gameboard(id):
    db = get_db().ddz
    game = db.games.find_one({'game_id': id})
    print(current_user)
    return render_template('game/game.html', game=game)

@socketio.on('connect')
def connectionMade():
    print('Connection occured! with ', current_user.username, request.sid)
    
@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', current_user.username)

@socketio.on('my event')
def handleCustomEvent(data):
    print('received from client', data)
    # emit('start game', "Starting the game now")

#
def initialize_game():
    deck = []
    for i in range(4):
        deck += list(range(3, 16))

    # add jokers 
    deck.append(16)
    deck.append(17)

    random.shuffle(deck)

    hands = [sorted(deck[:17]), sorted(deck[17:34]), sorted(deck[34:51]) ]
    blind = sorted(deck[51:])

    flipped_card = random.randint(0, 51)
    return {'hands': hands, 'blind': blind, 'flipped_card': flipped_card}
    # socketio.emit('deal cards', data=hands, broadcast=True)
    # game = db.games.find_one({'game_id': game_id})
    # game['cards'] = [] 

### Game state
# players
# cards 
# bids
# blind 
# currentPile