import random 

from flask_login import UserMixin
from flaskr.db import get_db


def get_random_unicode(length):

    get_char = chr

    # Update this to include code point ranges to be sampled
    include_ranges = [
        ( 0x0021, 0x0021 ),
        ( 0x0023, 0x0026 ),
        ( 0x0028, 0x007E ),
        ( 0x00A1, 0x00AC ),
        ( 0x00AE, 0x00FF ),
        ( 0x0100, 0x017F ),
        ( 0x0180, 0x024F ),
        ( 0x2C60, 0x2C7F ),
        ( 0x16A0, 0x16F0 ),
        ( 0x0370, 0x0377 ),
        ( 0x037A, 0x037E ),
        ( 0x0384, 0x038A ),
        ( 0x038C, 0x038C ),
    ]

    alphabet = [
        get_char(code_point) for current_range in include_ranges
            for code_point in range(current_range[0], current_range[1] + 1)
    ]
    return ''.join(random.choice(alphabet) for i in range(length))

class User(UserMixin):

    @property
    def is_authenticated(self):
        db = get_db().ddz
        record = db.users.find_one(
            {'username': self.username, 
             'password_hash': self.password_hash})
        
        if record is not None:
            self.id = str(record._id)

        return record is not None


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
        # finds user in db and returns object 
        db = get_db().ddz
        record = db.users.find_one({'_id': user_id})
        if record is not None:
            user = User()
            user.username = record.username
            user.password_hash = record.password_hash
            user.id = user_id
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
            user_id = db.users.insert_one(self.__dict__())
            self.id = str(user_id)
        return error
        

