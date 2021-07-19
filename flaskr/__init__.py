import os

from flask import Flask, g
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, emit
from flask_login import LoginManager

socketio = SocketIO()
login_manager = LoginManager()
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    # app.config["MONGO_URI"] = "mongodb+srv://joeschless:805858joe@cluster0.t4ie6.mongodb.net/ddz?retryWrites=true&w=majority"
    app.config["MONGO_URI"] = "mongodb://localhost:27017/"

    socketio.init_app(app)

    # login_manager = LoginManager()
    login_manager.login_view = "auth.login"

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db 
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import game
    app.register_blueprint(game.bp)

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')