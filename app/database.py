import os
import sqlite3

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_DB_PATH = os.path.join(BASE_DIR, "anime.db")
ANIME_CSV_PATH = os.path.join(BASE_DIR, "data", "anime_with_selected_genres.csv")


def get_connection():
    conn = sqlite3.connect(ANIME_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _anime_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='anime'")
    return cursor.fetchone() is not None


def ensure_anime_db(logger=None):
    os.makedirs(os.path.dirname(ANIME_DB_PATH), exist_ok=True)

    conn = sqlite3.connect(ANIME_DB_PATH)
    try:
        if _anime_table_exists(conn):
            return True

        if pd is None:
            if logger:
                logger.error("pandas is not installed; cannot auto-create anime table")
            return False

        if not os.path.exists(ANIME_CSV_PATH):
            if logger:
                logger.error("Anime CSV not found at %s", ANIME_CSV_PATH)
            return False

        df = pd.read_csv(ANIME_CSV_PATH)
        if df.empty:
            if logger:
                logger.error("Anime CSV is empty: %s", ANIME_CSV_PATH)
            return False

        df.to_sql("anime", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON anime(title)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_genres ON anime(genres)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON anime(score)")
        conn.commit()

        if logger:
            logger.info("Created anime table from CSV at startup")
        return True
    finally:
        conn.close()
