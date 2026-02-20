import os
import pandas as pd
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE_DIR, "data", "anime_with_selected_genres.csv")
db_path = os.path.join(BASE_DIR, "anime.db")

df = pd.read_csv(csv_path)

conn = sqlite3.connect(db_path)

df.to_sql("anime", conn, if_exists="replace", index=False)

# 🔥 ADD INDEXES (BIG PERFORMANCE BOOST)
conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON anime(title);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_genres ON anime(genres);")
conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON anime(score);")
conn.commit()

conn.close()

print("Database created successfully with indexes at:", db_path)
