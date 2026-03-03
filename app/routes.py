from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .recommender import get_recommendations, get_anime_by_genre
import sqlite3
import os
from app.models import Favorite
import random

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
    anime=anime.to_dict() if anime is not None else None,
    recommendations=recommendations.to_dict(orient="records") if recommendations is not None else []
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
    page = data.get("page", 1)
    per_page = 20

    if not selected_genres:
        return jsonify([])

    conn = sqlite3.connect(ANIME_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, genres, image_url, score FROM anime")
    rows = cursor.fetchall()
    conn.close()

    results = []

    selected_genres = [g.lower() for g in selected_genres]

    for row in rows:
        title, genres, image_url, score = row

        if not genres:
            continue

        anime_genres = [g.strip().lower() for g in genres.split(",")]

        if all(g in anime_genres for g in selected_genres):
            results.append({
                "title": title,
                "genres": genres,
                "image_url": image_url,
                "score": score
            })

    # 🔥 ADD PAGINATION
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results[start:end]

    return jsonify(paginated_results)


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


# ================= top ranking =================
@main.route("/top-rankings")
@login_required
def top_rankings():
    page = request.args.get("page", 1, type=int)
    per_page = 12
    offset = (page - 1) * per_page

    conn = sqlite3.connect("anime.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM anime
        WHERE score IS NOT NULL
        ORDER BY score DESC, RANDOM()
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    anime_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM anime WHERE score IS NOT NULL")
    total = cursor.fetchone()[0]
    conn.close()

    has_next = offset + per_page < total
    has_prev = page > 1

    return render_template(
        "index.html",
        top_rankings=anime_list,
        page=page,
        has_next=has_next,
        has_prev=has_prev
    )
@main.route("/add-favorite/<int:anime_id>")
@login_required
def add_favorite(anime_id):
    conn = sqlite3.connect("user_info.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO favorites (user_id, anime_id)
        VALUES (?, ?)
    """, (current_user.id, anime_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


@main.route("/add-favorite/<int:anime_id>")
@login_required
def add_favorite(anime_id):
    conn = sqlite3.connect("user_info.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO favorites (user_id, anime_id)
        VALUES (?, ?)
    """, (current_user.id, anime_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


@main.route("/add-favorite/<int:anime_id>")
@login_required
def add_favorite(anime_id):
    conn = sqlite3.connect("user_info.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO favorites (user_id, anime_id)
        VALUES (?, ?)
    """, (current_user.id, anime_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

# =================favourites =================

@main.route("/favorites")
@login_required
def favorites():
    conn = sqlite3.connect("user_info.db")
    cursor = conn.cursor()

    cursor.execute("SELECT anime_id FROM favorites WHERE user_id=?", (current_user.id,))
    anime_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not anime_ids:
        return render_template("index.html", favorite_list=[])

    conn2 = sqlite3.connect("anime.db")
    conn2.row_factory = sqlite3.Row
    cursor2 = conn2.cursor()

    query = f"""
        SELECT * FROM anime
        WHERE anime_id IN ({','.join(['?']*len(anime_ids))})
    """

    cursor2.execute(query, anime_ids)
    favorite_list = cursor2.fetchall()
    conn2.close()

    return render_template("index.html", favorite_list=favorite_list)