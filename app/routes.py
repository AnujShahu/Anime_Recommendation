from flask import Blueprint, render_template, request, jsonify
from .recommender import get_recommendations
import sqlite3
import pandas as pd
import os

main = Blueprint("main", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "anime.db")


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


# ✅ AUTOCOMPLETE ROUTE
@main.route("/get_anime_titles")
def get_anime_titles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT title FROM anime", conn)
    conn.close()

    titles = df["title"].dropna().tolist()

    # IMPORTANT: must return { titles: [...] }
    return jsonify({"titles": titles})


# ✅ GET ALL GENRES
@main.route("/get_genres")
def get_genres():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT genres FROM anime", conn)
    conn.close()

    all_genres = set()

    for genre_list in df["genres"].dropna():
        for genre in genre_list.split(","):
            all_genres.add(genre.strip())

    return jsonify(sorted(list(all_genres)))


@main.route("/search_by_genres", methods=["POST"])
def search_by_genres():
    data = request.get_json()
    selected_genres = data.get("genres", [])

    if not selected_genres:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Build SQL WHERE clause dynamically
    conditions = []
    values = []

    for genre in selected_genres:
        conditions.append("LOWER(genres) LIKE ?")
        values.append(f"%{genre.lower()}%")

    query = f"""
        SELECT title, genres, image_url, score
        FROM anime
        WHERE {" OR ".join(conditions)}
        LIMIT 20
    """

    cursor.execute(query, values)
    rows = cursor.fetchall()

    conn.close()

    # Convert to list of dicts
    results = [
        {
            "title": row[0],
            "genres": row[1],
            "image_url": row[2],
            "score": row[3]
        }
        for row in rows
    ]

    return jsonify(results)
