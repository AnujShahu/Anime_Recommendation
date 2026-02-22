from flask_login import UserMixin
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "anime.db")

class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = str(id)
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password FROM users WHERE id=?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if user:
            return User(*user)
        return None