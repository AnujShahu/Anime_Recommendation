from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .recommender import get_recommendations, get_anime_by_genre
import sqlite3
import os

main = Blueprint("main", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_DB_PATH = os.path.join(BASE_DIR, "anime.db")


# ================= HOME =================
@main.route("/")
def home():
    return render_template("index.html")


# ================= RECOMMEND =================
@main.route("/recommend", methods=["POST"])
def recommend():
    anime_name = request.form.get("anime_name")

    if not anime_name:
        flash("Please enter an anime name!")
        return redirect(url_for("main.home"))

    anime, recommendations = get_recommendations(anime_name)

    if anime is None:
        flash("Anime not found.")
        return redirect(url_for("main.home"))

    return render_template(
        "index.html",
        anime=anime,
        recommendations=recommendations.to_dict(orient="records")
    )


# ================= GET TITLES (FOR AUTOCOMPLETE) =================
@main.route("/get_anime_titles")
def get_anime_titles():
    conn = sqlite3.connect(ANIME_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM anime")
    titles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify({"titles": titles})


# ================= GET GENRES =================
@main.route("/get_genres")
def get_genres():
    conn = sqlite3.connect(ANIME_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT genres FROM anime")
    rows = cursor.fetchall()
    conn.close()

    genre_set = set()

    for row in rows:
        if row[0]:
            genres = row[0].split(",")
            for g in genres:
                genre_set.add(g.strip())

    return jsonify(sorted(list(genre_set)))


# ================= SEARCH BY GENRES =================
@main.route("/search_by_genres", methods=["POST"])
def search_by_genres():
    data = request.get_json()
    selected_genres = data.get("genres", [])

    conn = sqlite3.connect(ANIME_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, genres, image_url, score FROM anime")
    rows = cursor.fetchall()
    conn.close()

    results = []

    for row in rows:
        title, genres, image_url, score = row

        if not genres:
            continue

        anime_genres = [g.strip() for g in genres.split(",")]

        if all(g in anime_genres for g in selected_genres):
            results.append({
                "title": title,
                "genres": genres,
                "image_url": image_url,
                "score": score
            })

    return jsonify(results)


# ================= ADMIN DASHBOARD =================
@main.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("main.home"))

    from .user_service import USER_DB_PATH

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users)