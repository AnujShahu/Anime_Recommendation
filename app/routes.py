from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations
from .database import get_connection
from . import cache
import pandas as pd
import logging

main = Blueprint("main", __name__)


# ================= HOME ROUTE =================
@main.route("/", methods=["GET", "POST"])
def home():
    anime = None
    recommendations = None
    error = None

    if request.method == "POST":
        anime_name = request.form.get("anime_name")
        logging.info(f"Search requested: {anime_name}")

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


# ================= AUTOCOMPLETE =================
@main.route("/get_anime_titles")
@cache.cached(timeout=600)
def get_anime_titles():
    conn = get_connection()
    df = pd.read_sql_query("SELECT title FROM anime", conn)
    conn.close()

    titles = df["title"].dropna().tolist()
    return jsonify({"titles": titles})


# ================= GET GENRES =================
@main.route("/get_genres", methods=["GET"])
@cache.cached(timeout=600)
def get_genres():
    conn = get_connection()
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
    page = data.get("page", 1)
    per_page = 20

    if not selected_genres:
        return jsonify([])

    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT title, genres, image_url, score FROM anime",
        conn
    )
    conn.close()

    selected_genres = [g.lower() for g in selected_genres]

    def match_count(genre_string):
        if not genre_string:
            return 0

        genre_list = [g.strip().lower() for g in genre_string.split(",")]

        return sum(1 for g in selected_genres if g in genre_list)

    df["match_score"] = df["genres"].apply(match_count)

    filtered = df[df["match_score"] > 0]

    filtered = filtered.sort_values(
        by=["match_score", "score"],
        ascending=[False, False]
    )

    # 🔥 PAGINATION
    start = (page - 1) * per_page
    end = start + per_page

    results = filtered.iloc[start:end].to_dict(orient="records")

    logging.info(f"Genre search: {selected_genres}")

    return jsonify(results)
