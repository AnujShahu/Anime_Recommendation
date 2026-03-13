import sqlite3
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")


def init_user_db():
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL,
            UNIQUE(user_id, anime_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL,
            UNIQUE(user_id, anime_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            expires_at INTEGER NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        )
        """
    )

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
                (username, email, hashed_password),
            )
            conn.commit()
            return True, "Account created successfully!"
        except sqlite3.IntegrityError:
            return False, "Email already exists!"
        finally:
            conn.close()

    @staticmethod
    def get_user_by_email(email):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE email=?",
            (email,),
        )
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def get_user_by_id(user_id):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, role FROM users WHERE id=?",
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def update_password(email, new_password):
        hashed = generate_password_hash(new_password)
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed, email),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def create_password_reset(email, code, expires_at):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        code_hash = generate_password_hash(code)
        now_ts = int(time.time())

        cursor.execute("DELETE FROM password_resets WHERE email=?", (email,))
        cursor.execute(
            """
            INSERT INTO password_resets (email, code_hash, expires_at, attempts, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (email, code_hash, int(expires_at), now_ts),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def verify_password_reset(email, code, max_attempts=5):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, code_hash, expires_at, attempts FROM password_resets WHERE email=?",
            (email,),
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Invalid or expired code."

        reset_id, code_hash, expires_at, attempts = row
        now_ts = int(time.time())

        if now_ts > int(expires_at):
            cursor.execute("DELETE FROM password_resets WHERE id=?", (reset_id,))
            conn.commit()
            conn.close()
            return False, "Invalid or expired code."

        if attempts >= max_attempts:
            conn.close()
            return False, "Too many attempts. Request a new code."

        if not check_password_hash(code_hash, code):
            cursor.execute(
                "UPDATE password_resets SET attempts = attempts + 1 WHERE id=?",
                (reset_id,),
            )
            conn.commit()
            conn.close()
            return False, "Invalid code."

        conn.close()
        return True, "Code verified."

    @staticmethod
    def clear_password_reset(email):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM password_resets WHERE email=?", (email,))
        conn.commit()
        conn.close()
