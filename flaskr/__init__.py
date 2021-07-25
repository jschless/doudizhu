import os

from flask import Flask, g
from flask_pymongo import PyMongo
from flask_socketio import SocketIO, emit
from flask_login import LoginManager

from .config import mongodb_uri

socketio = SocketIO()
login_manager = LoginManager()
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        app.config.from_mapping(
            SECRET_KEY='dev',
            MONGO_URI=mongodb_uri
        )

    socketio.init_app(app)


    login_manager.init_app(app) 
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

    return app

app = create_app()