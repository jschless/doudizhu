import click
from flask import current_app, g
from flask.cli import with_appcontext
from flask_pymongo import PyMongo


def init_db():
    db = get_db()


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def get_db():
    if "db" not in g:
        mongo = PyMongo(current_app)
        g.db = mongo.cx  # this creates a database

    return g.db


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
