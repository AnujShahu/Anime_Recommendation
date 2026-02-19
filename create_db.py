import os
import pandas as pd
import sqlite3

# Get project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV path
csv_path = os.path.join(BASE_DIR, "data", "anime_with_selected_genres.csv")

# Load CSV
df = pd.read_csv(csv_path)

# SQLite database path
db_path = os.path.join(BASE_DIR, "anime.db")

# Create connection
conn = sqlite3.connect(db_path)

# Save to database
df.to_sql("anime", conn, if_exists="replace", index=False)

conn.close()

print("Database created successfully at:", db_path)
