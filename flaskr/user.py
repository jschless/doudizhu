import random 

from flask_login import UserMixin
from flaskr.db import get_db
from bson.objectid import ObjectId


class User(UserMixin):

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.username

    def get_id(self):
        try:
            return self.id
        except AttributeError:
            return None

    def __dict__(self):
        return {
            'username': self.username, 
            'password_hash': self.password_hash
            }

    @classmethod
    def get(cls, user_id):
        if user_id is None or user_id == "None":
            return None
        # finds user in db and returns object 
        db = get_db().ddz
        record = db.users.find_one({'_id': ObjectId(user_id)})
        if record is not None:
            user = User()
            user.username = record['username']
            user.password_hash = record['password_hash']
            user.id = user_id
            return user
        else:
            return None
    
    def check_username_availability(self):
        # returns True if username is available
        db = get_db().ddz
        record = db.users.find_one({'username': self.username})
        return record is None

    def save(self):
        error = None
        if not self.check_username_availability():
            error = 'Username already taken.'
        else:
            db = get_db().ddz
            user_id = db.users.insert_one(self.__dict__()).inserted_id
            self.id = str(user_id)
        return error
        

