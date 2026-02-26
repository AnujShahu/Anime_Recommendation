import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")


def init_user_db():
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        anime_title TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


class UserService:

    @staticmethod
    def create_user(username, email, password):
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, 'user')",
                (username, email, hashed_password)
            )
            conn.commit()
            return True, "Account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Email already exists!"
        finally:
            conn.close()

    @staticmethod
    def authenticate_user(email, password):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            return user
        return None

    @staticmethod
    def get_user_by_id(user_id):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE id=?",
            (user_id,)
        )

        user = cursor.fetchone()
        conn.close()

        return user