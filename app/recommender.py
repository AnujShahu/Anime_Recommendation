import pandas as pd
import os

# Locate CSV file properly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "anime_with_selected_genres.csv")

data = pd.read_csv(csv_path)

# Clean dataset
data["genre"] = data["genre"].fillna("")
data["score"] = pd.to_numeric(data["score"], errors="coerce").fillna(0)
data["popularity"] = pd.to_numeric(data["popularity"], errors="coerce").fillna(999999)
data["title"] = data["title"].astype(str)

def get_recommendations(anime_title):
    if not anime_title:
        return []

    matched = data[data["title"].str.lower() == anime_title.lower()]

    if matched.empty:
        return []

    selected = matched.iloc[0]

    selected_genre = selected["genre"].split(",")[0]
    selected_type = selected["type"]

    filtered = data[
        (data["genre"].str.contains(selected_genre, na=False)) &
        (data["type"] == selected_type) &
        (data["title"].str.lower() != anime_title.lower())
    ]

    filtered = filtered.sort_values(
        by=["score", "popularity"],
        ascending=[False, True]
    )

    recommendations = filtered.head(6)[
        ["title", "genre", "score", "popularity", "type", "episodes"]
    ]

    return recommendations.to_dict(orient="records")
