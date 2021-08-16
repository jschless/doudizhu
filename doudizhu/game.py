from . import socketio

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_from_directory,
)

from flask_login import current_user, login_required
from flask_socketio import join_room

from .game_class import Game

bp = Blueprint("game", __name__, url_prefix="/")


@bp.route("", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        error = None
        game = None
        if "create" in request.form:
            game = Game.create_game()
            game_id = game.game_id
        elif "join" in request.form:
            game_id = request.form["gamecode"]
            try:
                game = Game(game_id)
            except KeyError:
                error = "No game exists with that code"
            else:
                if current_user in game.players:
                    print("player re-entering room")
                elif len(game.players) == 3:
                    error = "Game is full"

        # TODO add a leave room option

        if error is None:
            return redirect(url_for(".gameboard", id=game_id))

        flash(error)
    return render_template("game/create_game.html")


@bp.route("/favicon.ico", methods=["GET"])
def icon():
    return send_from_directory(
        "static", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


@login_required
@bp.route("/<id>", methods=("GET", "POST"))
def gameboard(id):
    game = Game(id).to_mongo()
    return render_template("game/game.html", game=game)


@socketio.on("add to database")
def add_to_db(data):
    if current_user.is_authenticated:
        current_user.update_sid(request.sid)
        game = Game(data["game_id"])
        game.add_player_to_game(current_user)
        join_room(data["game_id"])
        socketio.send(f"successfully added {data['username']} to database")
    else:
        print("Refusing connection with unauthenticated user")
        return False  # not allowed here


@socketio.on("disconnect")
def disconnect_user():
    pass
    # game_id = request.referrer[-5:]
    # game = Game(game_id)
    # game.remove_player_from_game(current_user)


@socketio.on("next round")
def run_round(data):
    game = Game(data["game_id"])
    game.initialize_round()


@socketio.on("test round")
def run_round(data):
    game = Game(data["game_id"])
    game.initialize_test_round()


@socketio.on("submit bid")
def add_bid(data):
    game = Game(data["game_id"])
    game.register_bid(data)


@socketio.on("next hand")
def get_move(data):
    game = Game(data["game_id"])
    game.get_move()


@socketio.on("submit move")
def add_move(data):
    game = Game(data["game_id"])
    game.register_move(data)


@socketio.on("chat")
def received_chat(data, methods=["GET", "POST"]):
    socketio.emit("chat broadcast", data, to=data["game_id"])
