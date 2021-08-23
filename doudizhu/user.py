from flask_login import UserMixin
from doudizhu.db import get_db
from bson.objectid import ObjectId


class User(UserMixin):
    def __init__(self, username: str, password_hash: str):
        super().__init__()
        self.username = username
        self.password_hash = password_hash
        self.lifetime_score = 0
        self.game_id = None
        self.sid = None

        self.clear_temporary_variables()

    @classmethod
    def from_record(cls, record):
        user = User(record["username"], record["password_hash"])
        for key, value in record.items():
            setattr(user, key, value)
        return user

    @property
    def is_authenticated(self):
        return True

    def clear_temporary_variables(self):
        """Initializes variables for each game"""
        self.hand = []
        self.visible_cards = []
        self.bid = None
        self.last_move = []
        self.last_discard = []

    def __str__(self):
        return self.username

    def get_id(self):
        try:
            return self.id
        except AttributeError:
            return None

    def asdict(self):
        dict_vars = [
            "username",
            "password_hash",
            "game_id",
            "sid",
            "hand",
            "visible_cards",
            "bid",
            "last_move",
            "last_discard",
        ]
        temp = {k: getattr(self, k) for k in dict_vars}
        temp["_id"] = ObjectId(self._id)
        return temp

    @classmethod
    def get(cls, user_id):
        if user_id is None or user_id == "None":
            return None
        # finds user in db and returns object
        db = get_db().ddz
        record = db.users.find_one({"_id": ObjectId(user_id)})
        if record is not None:
            user = User.from_record(record)
            user.id = user_id
            return user
        else:
            return None

    def check_username_availability(self):
        # returns True if username is available
        db = get_db().ddz
        record = db.users.find_one({"username": self.username})
        return record is None

    def update_db(self):
        """Updates the user entry in the database"""
        get_db().ddz.users.replace_one({"username": self.username}, self.asdict())

    def save(self):
        error = None
        if not self.check_username_availability():
            error = "Username already taken."
        else:
            db = get_db().ddz
            user_id = db.users.insert_one(
                {"username": self.username, "password_hash": self.password_hash}
            ).inserted_id
            self._id = str(user_id)
            self.update_db()
        return error

    def join_game(self, game_id):
        """Sets the game id for a given user"""
        if self.game_id is None:
            self.game_id = game_id
            self.update_db()
        elif game_id != self.game_id:
            self.game_id = game_id
            # TODO leave other game
            # raise RuntimeError("User is already in a game")
        print(f"{self.username} joining game {self.game_id}")

    def leave_game(self, game_id):
        self.game_id = None

    def __eq__(self, other):
        return self.username == other.username

    def update_sid(self, sid):
        self.sid = sid
        self.update_db()

    def update_scoreboard(self, score):
        self.lifetime_score += score
        self.update_db()
