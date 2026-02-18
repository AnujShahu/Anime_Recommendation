def get_recommendations(anime_name):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM anime", conn)

    df["title"] = df["title"].astype(str).str.strip()

    anime_name = anime_name.strip().lower()

    if not anime_name:
        conn.close()
        return None, None

    match = df[df["title"].str.lower().str.contains(anime_name, na=False)]

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
        recommendations["title"].str.lower() != anime_name
    ].head(5)

    conn.close()

    return anime_row, recommendations
