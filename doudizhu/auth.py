from flask import Blueprint, flash, redirect, render_template, request, url_for

from flask_login import login_user, logout_user, login_required
from doudizhu.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash

from . import login_manager
from .loginform import LoginForm
from .user import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@bp.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        db = get_db().ddz
        password = form.password.data
        user = User(form.username.data, generate_password_hash(password))
        error = None

        if "create" in request.form:
            print("User created")
            error = user.save()

        if "login" in request.form or error is None:
            # Check credentials
            db = get_db().ddz
            record = db.users.find_one({"username": user.username})
            if record is None:
                error = "Username does not exist"
            else:
                # username exists, validate password
                correct_password = check_password_hash(
                    record["password_hash"], password
                )
                if correct_password:
                    # password is correct, set the id and login
                    user.id = str(record["_id"])
                    login_success = login_user(user, remember=True)
                    if login_success:
                        flash("Login successful")
                        next = request.args.get("next")
                else:
                    error = "Incorrect credentials"

        if error is None:
            # print('redirecting to', next, next or url_for(''), url_for(''))
            return redirect(next or url_for("game.create"))

        flash(error)
    else:
        flash("Please fill out the form properly. Usernames must be 4 characters!")

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("game.create"))
