import pytest
from flask import session
from flaskr.db import get_db
from flask_login import current_user
from flaskr.loginform import LoginForm


def test_create(client, app):
    with app.app_context():  # remove user
        get_db().ddz.users.delete_one({"username": "testsuite"})

    assert client.get("/auth/login").status_code == 200
    form = LoginForm(username="testsuite", password="testsuite")
    response = client.post(
        "/auth/login", data={**form.data, "create": "Create Account"}
    )

    # user should be redirected to index
    assert "http://localhost/" == response.headers["Location"]

    with app.app_context():  # check whether user was created
        assert get_db().ddz.users.find_one({"username": "testsuite"}) is not None


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("", "", b"Please fill out the form properly. Usernames must be 4 characters!"),
        (
            "a",
            "",
            b"Please fill out the form properly. Usernames must be 4 characters!",
        ),
        ("testing", "test", b"Username already taken."),
    ),
)
def test_register_validate_input(client, username, password, message):
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password, "create": "Create Account"},
    )
    assert message in response.data


def test_login(client, auth):
    assert client.get("/auth/login").status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "http://localhost/"

    with client:
        client.get("/")
        assert current_user.username == "testing"


@pytest.mark.parametrize(
    ("username", "password", "message"),
    (
        ("pester", "test", b"Username does not exist"),
        ("testing", "a", b"Incorrect credentials"),
    ),
)
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data


def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert "user_id" not in session
