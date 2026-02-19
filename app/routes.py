from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations
import sqlite3
import pandas as pd
import os

main = Blueprint("main", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "anime.db")


# ================= HOME ROUTE =================
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


# ================= AUTOCOMPLETE ROUTE =================
@main.route("/get_anime_titles")
def get_anime_titles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT title FROM anime", conn)
    conn.close()

    titles = df["title"].dropna().tolist()

    return jsonify({"titles": titles})


# ================= GET GENRES ROUTE =================
@main.route("/get_genres", methods=["GET"])
def get_genres():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT genres FROM anime", conn)
    conn.close()

    all_genres = set()

    for genre_string in df["genres"].dropna():
        for genre in genre_string.split(","):
            cleaned = genre.strip()
            if cleaned:
                all_genres.add(cleaned)

    return jsonify(sorted(list(all_genres)))


# ================= SEARCH BY GENRES =================
@main.route("/search_by_genres", methods=["POST"])
def search_by_genres():
    data = request.get_json()
    selected_genres = data.get("genres", [])

    if not selected_genres:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT title, genres, image_url, score FROM anime",
        conn
    )
    conn.close()

    # Convert selected genres to lowercase once
    selected_genres = [g.lower() for g in selected_genres]

    def match_count(genre_string):
        if not genre_string:
            return 0

        genre_list = [
            g.strip().lower()
            for g in genre_string.split(",")
        ]

        # Exact matching only
        return sum(
            1 for g in selected_genres
            if g in genre_list
        )

    df["match_score"] = df["genres"].apply(match_count)

    # Keep only anime with at least 1 matching genre
    filtered = df[df["match_score"] > 0]

    # Sort by:
    # 1️⃣ number of matched genres (descending)
    # 2️⃣ rating score (descending)
    filtered = filtered.sort_values(
        by=["match_score", "score"],
        ascending=[False, False]
    )

    results = filtered.head(20).to_dict(orient="records")

    return jsonify(results)
