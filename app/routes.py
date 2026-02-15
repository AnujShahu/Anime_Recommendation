from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations
import sqlite3
import pandas as pd

main = Blueprint("main", __name__)

DB_PATH = "anime.db"


# ================= HOME =================
@main.route("/", methods=["GET", "POST"])
def home():
    anime = None
    recommendations = None
    error = None

    if request.method == "POST":
        anime_name = request.form.get("anime_name")

        anime_data, recs = get_recommendations(anime_name)

        if anime_data is None:
            error = "Anime not found!"
        else:
            anime = anime_data.to_dict()
            recommendations = recs.to_dict(orient="records")

    return render_template(
        "index.html",
        anime=anime,
        recommendations=recommendations,
        error=error
    )


# ================= GET ALL TITLES (FOR AUTOCOMPLETE) =================
@main.route("/get_anime_titles")
def get_anime_titles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT title FROM anime", conn)
    conn.close()

    titles = df["title"].dropna().tolist()
    return jsonify({"titles": titles})


# ================= GET GENRES =================
@main.route("/get_genres")
def get_genres():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT genres FROM anime", conn)
    conn.close()

    genre_set = set()

    for g in df["genres"]:
        if g:
            for genre in g.split(","):
                genre_set.add(genre.strip())

    return jsonify(sorted(list(genre_set)))


# ================= SEARCH BY GENRES =================
@main.route("/search_by_genres", methods=["POST"])
def search_by_genres():
    selected_genres = request.json.get("genres", [])

    if not selected_genres:
        return jsonify([])

    selected_genres = [g.lower() for g in selected_genres]

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM anime", conn)
    conn.close()

    def has_all_genres(g):
        if not g:
            return False
        g = g.lower()
        return all(genre in g for genre in selected_genres)

    filtered = df[df["genres"].apply(has_all_genres)]

    results = filtered.head(20).to_dict(orient="records")

    return jsonify(results)
