import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, 
    request, session, url_for, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

from flask_login import login_user
from flaskr.db import get_db

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
        user.password_hash = generate_password_hash(form.password.data)
        error = None
        
        if 'create' in request.form:
            print('User created')
            error = user.save() 
        
        if 'login' in request.form or error is None:
            # If there's a login request, or creating the user worked 
            login_success = login_user(user, remember=True)
            if login_success:
                flash("Login successful")
                next = request.args.get('next')
                
        if error is None:
            return redirect(next or url_for('index'))

        flash(error)

    return render_template('auth/login.html', form=form)