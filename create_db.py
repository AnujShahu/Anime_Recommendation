import os
import psycopg2
import sqlalchemy
import pandas as pd
import os

# Get current directory (project root)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build full path to CSV
csv_path = os.path.join(BASE_DIR, "data", "anime_with_selected_genres.csv")

# Load CSV
df = pd.read_csv(csv_path)

# Create SQLite database
db_path = os.path.join(BASE_DIR, "anime.db")

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = sqlalchemy.create_engine(DATABASE_URL)

df.to_sql("anime", conn, if_exists="replace", index=False)

conn.close()

print("Database created successfully at:", db_path)
