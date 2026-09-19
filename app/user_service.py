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
            role TEXT DEFAULT 'user',
            preferred_genres TEXT DEFAULT ''
        )
        """
    )

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_genres TEXT DEFAULT ''")
    except Exception:
        pass

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
                "INSERT INTO users (username, email, password, role, preferred_genres) VALUES (?, ?, ?, 'user', '')",
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
            "SELECT id, username, email, password, role, preferred_genres FROM users WHERE email=?",
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
            "SELECT id, username, email, password, role, preferred_genres FROM users WHERE id=?",
            (user_id,),
        )
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def get_user_stats(user_id):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM favorites WHERE user_id=?", (user_id,))
        favorites_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM watchlist WHERE user_id=?", (user_id,))
        watchlist_count = cursor.fetchone()[0]

        cursor.execute("SELECT id, username, email, role, preferred_genres FROM users WHERE id=?", (user_id,))
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            return None

        pref_genres = [g.strip() for g in (user_row[4] or "").split(",") if g.strip()]
        return {
            "id": user_row[0],
            "username": user_row[1],
            "email": user_row[2],
            "role": user_row[3],
            "preferred_genres": pref_genres,
            "favorites_count": favorites_count,
            "watchlist_count": watchlist_count,
        }

    @staticmethod
    def update_preferred_genres(user_id, genres_list):
        genres_str = ", ".join(genres_list) if isinstance(genres_list, list) else str(genres_list)
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET preferred_genres=? WHERE id=?", (genres_str, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def change_password(user_id, current_password, new_password):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "User not found."

        current_hash = row[0]
        if not check_password_hash(current_hash, current_password):
            conn.close()
            return False, "Current password is incorrect."

        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user_id))
        conn.commit()
        conn.close()
        return True, "Password updated successfully!"

    @staticmethod
    def delete_user_account(user_id):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM favorites WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM watchlist WHERE user_id=?", (user_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        return True

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
    def update_role_by_email(email, role):
        conn = sqlite3.connect(USER_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET role=? WHERE email=?",
            (role, email),
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
