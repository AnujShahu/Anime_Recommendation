from flask_login import UserMixin
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(BASE_DIR, "anime.db")


class User(UserMixin):
    def __init__(self, id, username, email, password, role="user"):
        self.id = str(id)
        self.username = username
        self.email = email
        self.password = password
        self.role = role  # NEW: role support


    # ================= GET USER BY ID =================
    @staticmethod
    def get(user_id):
        conn = sqlite3.connect(db_path)
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


    # ================= GET USER BY USERNAME =================
    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE username=?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            return User(*user)
        return None


    # ================= COUNT USERS =================
    @staticmethod
    def count_users():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count


    # ================= GET ALL USERS =================
    @staticmethod
    def get_all_users():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, password, role FROM users")
        users = cursor.fetchall()
        conn.close()

        return [User(*user) for user in users]


    # ================= PROMOTE TO ADMIN =================
    @staticmethod
    def promote_to_admin(user_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role='admin' WHERE id=?",
            (user_id,)
        )
        conn.commit()
        conn.close()