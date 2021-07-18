import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, 
    request, session, url_for, abort, send_from_directory
)

from flask_login import login_user, logout_user, login_required
from flaskr.db import get_db
from werkzeug.security import check_password_hash, generate_password_hash

from bson import json_util
from . import login_manager
from .loginform import LoginForm
from .user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        db = get_db().ddz
        user = User()
        user.username = form.username.data
        user.password = form.password.data
        error = None

        if 'create' in request.form:
            print('User created')
            error = user.save() 

        if 'login' in request.form or error is None:
            # Check credentials
            db = get_db().ddz
            record = db.users.find_one({'username': user.username})
            if record is None:
                error = "Username does not exist"
            else:
                # username exists, validate password
                correct_password = check_password_hash(record['password_hash'], user.password)
                if correct_password:
                    # password is correct, set the id and login
                    user.id = str(record['_id'])
                    login_success = login_user(user, remember=True)
                    if login_success:
                        flash("Login successful")
                        next = request.args.get('next')
                else:
                    error = "Incorrect credentials"
                
        if error is None:
            print('redirecting to', next, next or url_for('index'), url_for('index'))
            return redirect(next or url_for('index'))

        flash(error)

    return render_template('auth/login.html', form=form)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))