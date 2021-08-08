import pytest

from flaskr import create_app, socketio
from flaskr.db import get_db, init_db
from flaskr.game_class import Game


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "MONGO_URI": "mongodb://localhost:27017/",
            "SECRET_KEY": "dev",
        }
    )

    with app.app_context():
        init_db()
        get_db()

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def socketio_server():
    return socketio


@pytest.fixture
def test_game(app):
    with app.app_context():
        return Game("XM1P8")


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username="testing", password="testing"):
        return self._client.post(
            "/auth/login",
            data={"username": username, "password": password, "login": "Log in"},
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
