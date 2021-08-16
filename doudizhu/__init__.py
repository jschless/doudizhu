import os

from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager

socketio = SocketIO(cors_allowed_origins="*")
login_manager = LoginManager()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is not None:
        app.config.from_mapping(test_config)
    else:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("secret", "dev"),
            MONGO_URI=os.environ.get("mongodb_uri", "mongodb://localhost:27017/"),
        )

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

    socketio.init_app(app)

    return app


if __name__ == "flaskr":
    app = create_app()
