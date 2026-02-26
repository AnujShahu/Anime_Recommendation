import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")

conn = sqlite3.connect(USER_DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    print("✅ Role column added successfully!")
except Exception as e:
    print("⚠ Column may already exist:", e)

conn.commit()
conn.close()