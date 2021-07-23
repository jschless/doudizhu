import functools
import random
import time
import string
from pprint import pprint

from flask_login.utils import login_required

from . import socketio

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, send_from_directory
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import current_user, login_required
from flask_socketio import emit
from flaskr.db import get_db

from .utils import validate_type, validate_discard
from .game_class import Game

bp = Blueprint('game', __name__, url_prefix='/')


@bp.route('', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        error = None
        game = None
        db = get_db().ddz
        if 'create' in request.form:
            game = Game.create_game()
            game_id = game.game_id
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            try:
                game = Game(game_id)
            except KeyError:
                error = "No game exists with that code"
            else:
                if session['_user_id'] in [x['user_id'] for x in game['players']]:
                    print('player re-entering room')
                elif len(game['players']) == 3:
                    error = "Game is full"
                else:
                    # add player to game on connection
                    print('player has successfully joined')

        # TODO add a leave room option

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')


@bp.route('/favicon.ico', methods=['GET'])
def icon():
    return send_from_directory('static',
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@login_required
@bp.route('/<id>', methods=('GET', 'POST'))
def gameboard(id):
    print('gameboard id', id)
    game = Game(id).__dict__
    print('sending game to template', game)
    return render_template('game/game.html', game=game)


@socketio.on('connect')
def connectionMade():
    print('connection made', current_user)
    # print('Connection occured! with type ', type(current_user), current_user.username, request.sid)


@socketio.on('add to database')
def add_to_db(data):
    game = Game(data['game_id'])
    game.add_player_to_db(current_user, session, request)


@socketio.on('debug')
def debug(data):
    """For random functions I want to test out, so that I can activate them on click"""
    run_round(data['game_id'])
    # update_game(get_game(data['game_id']))


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', current_user)


@socketio.on('next round')
def run_round(game_id):
    print('running a round')
    initialize_game(game_id)


def initialize_game(game_id):
    game = Game(game_id)
    game.initialize_round()


def get_bid(game_id, minimum: int, first_bid: bool = False):
    game = Game(game_id)
    game.get_bid()


@socketio.on("submit bid")
def add_bid(data):
    game = Game(data['info']['game_id'])
    game.register_bid(data)


@socketio.on("next hand")
def get_move(game_id):
    game = Game(game_id)
    game.get_move()


@socketio.on("submit move")
def add_move(data):
    game = Game(data['info']['game_id'])
    game.register_move(data)
