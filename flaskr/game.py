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
                    print('creating game with id', game_id)
                    print(session)
                    record = {'game_id': game_id, 
                              'players': [
                                  {
                                      'user_id': session['_user_id'], 
                                      'username': current_user.username
                                  }
                                  ],
                              'n_players': 1
                              }
                    # player = Player(session['username'], session['user_id'])
                    # game = Game(player, game_id)
                    db.games.insert_one(record)
                    break
            
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            game = db.games.find_one({'game_id': game_id})
            if game['n_players'] == 3: # this is just for DEBUG
                run_game(game_id)
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
                db.games.replace_one({'game_id': game_id}, game)
                if game['n_players'] == 3:
                    run_game(game_id)

        ## TODO add a leave room option 

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')

@bp.route('/<id>', methods=('GET', 'POST'))
def gameboard(id):
    db = get_db().ddz
    game = db.games.find_one({'game_id': id})
    print(current_user)
    if request.method == 'POST':
        print('Clicked the start game button')

    return render_template('game/game.html', game=game)

@socketio.on('connect')
def connectionMade():
    print('Connection occured! with ', current_user.username, request.sid)

@socketio.on('add to database')
def add_to_db(data):
    print(data)
    print('adding to database')
    game = get_game(data['game_id'])
    print(game)
    for player in game['players']:
        if player['username'] == data['username']:
            player['socketid'] = request.sid
    update_game(game)


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', current_user.username)

@socketio.on('remove from database')
def removeFromDB(data):
    print("Not implemented yet")

def run_game(game_id):
    print('running a game')
    initialize_game(game_id)
    begin_bidding(game_id)

def initialize_game(game_id):
    print('dealing cards and initializing game')
    db = get_db().ddz
    game = db.games.find_one({'game_id': game_id})

    deck = []
    for i in range(4):
        deck += list(range(3, 16))

    # add jokers 
    deck.append(16)
    deck.append(17)

    random.shuffle(deck)

    hands = [sorted(deck[:17]), sorted(deck[17:34]), sorted(deck[34:51])]
    for h, p in zip(hands, game['players']):
        p['hand'] = h

    game['blind'] = sorted(deck[51:])
    game['flipped_card'] = random.randint(0, 51)

    db.games.replace_one({'game_id': game_id}, game)
    socketio.emit('cards dealt', "hello")

def begin_bidding(game_id):
    print('starting bidding')
    game = get_game(game_id)
    for p in game['players']:
        print('Sending bid request to ', p['username'])
        socketio.emit('bid')#, to=p['socketid'])
        # while True:
        #     # check every second whether we have received the bid
        #     time.sleep(1)
        #     new_game = get_game(game_id)
        #     for p2 in new_game['players']:
        #         if p['username'] == p2['username'] and 'bid' in p:
        #             socketio.emit('update gameboard')
        #             break
    
    # game = get_game(game_id)
    # winner = None
    # current_high_bid = 0
    # for p in game['players']:
    #     if p['bid'] > current_high_bid:
    #         winner = p
    # print('bidding complete. Landlord is: ', p)

def get_game(game_id):
    return get_db().ddz.games.find_one({'game_id': game_id})

def update_game(game):
    return get_db().ddz.games.replace_one({'game_id': game['game_id']}, game)

@socketio.on("submit bid")
def add_bid(data):
    print('received a bid', data)
    game = get_game(data['info']['game_id'])
    for p in game['players']:
        if p['username'] == data['info']['username']:
            p['bid'] = data['bid']
    update_game(game)        