import pandas as pd

# Load dataset once
data = pd.read_csv("data/anime_with_selected_genres.csv")

# Clean columns
data["genre"] = data["genre"].fillna("")
data["score"] = pd.to_numeric(data["score"], errors="coerce").fillna(0)
data["popularity"] = pd.to_numeric(data["popularity"], errors="coerce").fillna(999999)

def get_recommendations(anime_title):
    if anime_title not in data["title"].values:
        return []

    selected = data[data["title"] == anime_title].iloc[0]

    selected_genre = selected["genre"].split(",")[0]
    selected_type = selected["type"]

    filtered = data[
        (data["genre"].str.contains(selected_genre, na=False)) &
        (data["type"] == selected_type) &
        (data["title"] != anime_title)
    ]

    filtered = filtered.sort_values(
        by=["score", "popularity"],
        ascending=[False, True]
    )

    recommendations = filtered.head(6)[
        ["title", "genre", "score", "popularity", "type", "episodes", "image_url"]
    ]

    return recommendations.to_dict(orient="records")


