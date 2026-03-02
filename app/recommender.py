import pandas as pd
from .database import get_connection   # keep your existing connection logic


# ===============================
# RECOMMENDATION FUNCTION
# ===============================
def get_recommendations(anime_name):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM anime", conn)

    df["title"] = df["title"].astype(str).str.strip()
    anime_name_clean = anime_name.strip().lower()

    if not anime_name_clean:
        conn.close()
        return None, None

    match = df[df["title"].str.lower().str.contains(anime_name_clean, na=False)]

    if match.empty:
        conn.close()
        return None, None

    anime_row = match.iloc[0]

    if not anime_row["genres"]:
        conn.close()
        return anime_row, pd.DataFrame()

    genres = [g.strip().lower() for g in anime_row["genres"].split(",")]

    def has_common_genre(g):
        if not g:
            return False
        g = g.lower()
        return any(genre in g for genre in genres)

    recommendations = df[df["genres"].apply(has_common_genre)]

    recommendations = recommendations[
        recommendations["title"].str.lower() != anime_name_clean
    ].head(5)

    conn.close()

    return anime_row, recommendations


# ===============================
# BROWSE BY GENRE FUNCTION
# ===============================
def get_anime_by_genre(genre):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM anime", conn)

    genre = genre.strip().lower()

    if not genre:
        conn.close()
        return []

    def genre_match(g):
        if not g:
            return False
        return genre in g.lower()

    filtered = df[df["genres"].apply(genre_match)]

    conn.close()

    # Return as list of dictionaries (safe for template rendering)
    return filtered.to_dict(orient="records")