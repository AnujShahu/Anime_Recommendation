import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")

username = "YOUR_USERNAME_HERE"  # ← CHANGE THIS

conn = sqlite3.connect(USER_DB_PATH)
cursor = conn.cursor()

cursor.execute("UPDATE users SET role='superadmin' WHERE username=?", (username,))
conn.commit()

print("👑 You are now SUPERADMIN!")

conn.close()