from flask_login import UserMixin
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")


class User(UserMixin):
    def __init__(self, id, username, email, password, role="user"):
        self.id = str(id)
        self.username = username
        self.email = email
        self.password = password
        self.role = role

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE id=?",
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            return User(*user)
        return None

    @staticmethod
    def count_all():
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def count_admins():
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role IN ('admin','superadmin')")
        count = cursor.fetchone()[0]
        conn.close()
        return count
   @property
def is_admin(self):
    return self.role in ["admin", "superadmin"]

    @staticmethod
    def get_recent_users(limit=5):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, role FROM users ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        users = cursor.fetchall()
        conn.close()
        return users