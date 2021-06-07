import functools
import random
import string
from pprint import pprint

from . import socketio

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('game', __name__, url_prefix='/game')

@bp.route('/create', methods=('GET', 'POST'))
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
                    print('creating game with id', game_id)
                    db.games.insert_one({'game_id': game_id})
                    break
            
        elif 'join' in request.form:
            game_id = request.form['gamecode']
            game = db.games.find_one({'game_id': game_id})
            if game is None:
                error = "No game exists with that code"

        if error is None:
            return redirect(url_for(f'.gameboard', id=game_id))

        flash(error)
    return render_template('game/create_game.html')

@bp.route('/<id>', methods=('GET',))
def gameboard(id):
    db = get_db().ddz
    game = db.games.find_one({'game_id': id})
    return render_template('game/game.html', game=game)

@socketio.on('connect')
def connectionMade():
    print('Connection occured! with ', session['username'])