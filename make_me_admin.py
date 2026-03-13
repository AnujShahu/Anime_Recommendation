import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")

# Set the target by email (recommended)
email = "anujshahu1607@gmail.com"

# Optional: change username
new_username = None  # e.g., "Anuj"

# Choose role: "user", "admin", or "superadmin"
new_role = "superadmin"

conn = sqlite3.connect(USER_DB_PATH)
cursor = conn.cursor()

if new_username:
    cursor.execute("UPDATE users SET username=? WHERE email=?", (new_username, email))

cursor.execute("UPDATE users SET role=? WHERE email=?", (new_role, email))

conn.commit()
conn.close()

print("User updated.")
