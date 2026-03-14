from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .recommender import get_recommendations
from .anilist_api import search_anime
import sqlite3
import os
import math

main = Blueprint("main", __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIME_DB_PATH = os.path.join(BASE_DIR, "anime.db")
USER_DB_PATH = os.path.join(BASE_DIR, "user_info.db")


def _is_ajax_request():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _is_superadmin():
    return current_user.is_authenticated and current_user.role == "superadmin"


# ================= HOME =================
@main.route("/")
def home():
    return render_template("index.html", page_mode="home")


# ================= RECOMMEND =================
@main.route("/recommend", methods=["POST"])
def recommend():
    anime_name = request.form.get("anime_name")
    status = (request.form.get("status") or "").strip().upper()

    if not anime_name and not status:
        flash("Please enter an anime name or choose a status.")
        return redirect(url_for("main.home"))

    anime = None
    recommendations = None

    if anime_name and not status:
        anime, recommendations = get_recommendations(anime_name)

    if anime is None:
        live_results = search_anime(anime_name, status=status or None)
        if live_results:
            return render_template(
                "index.html",
                page_mode="home",
                live_results=live_results,
                live_status=status or "ANY",
            )
        flash("No results found in local data or live API.")
        return redirect(url_for("main.home"))

    return render_template(
        "index.html",
        page_mode="home",
        anime=anime.to_dict() if anime is not None else None,
        recommendations=recommendations.to_dict(orient="records") if recommendations is not None else [],
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
            for genre in genres:
                genre_set.add(genre.strip())

    return jsonify(sorted(list(genre_set)))


# ================= SEARCH BY GENRES =================
@main.route("/search_by_genres", methods=["POST"])
def search_by_genres():
    data = request.get_json() or {}
    selected_genres = data.get("genres", [])
    page = int(data.get("page", 1))
    per_page = 20

    if not selected_genres:
        return jsonify([])

    conn = sqlite3.connect(ANIME_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT anime_id, title, genres, image_url, score FROM anime")
    rows = cursor.fetchall()
    conn.close()

    results = []
    selected_genres = [genre.lower() for genre in selected_genres]

    for row in rows:
        anime_id, title, genres, image_url, score = row
        if not genres:
            continue

        anime_genres = [genre.strip().lower() for genre in genres.split(",")]
        if all(genre in anime_genres for genre in selected_genres):
            results.append(
                {
                    "anime_id": anime_id,
                    "title": title,
                    "genres": genres,
                    "image_url": image_url,
                    "score": score,
                }
            )

    start = (page - 1) * per_page
    end = start + per_page
    return jsonify(results[start:end])


# ================= ADMIN DASHBOARD =================
@main.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("main.home"))

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    conn.close()

    total_users = len(users)
    total_admins = sum(1 for user in users if user[3] in ("admin", "superadmin"))
    recent_users = sorted(users, key=lambda user: user[0], reverse=True)[:5]

    return render_template(
        "admin_dashboard.html",
        users=users,
        total_users=total_users,
        total_admins=total_admins,
        recent_users=recent_users,
    )


@main.route("/admin-users")
@login_required
def admin_users():
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("main.home"))

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    return render_template("users.html", users=users)


@main.route("/superadmin")
@login_required
def superadmin_panel():
    if not _is_superadmin():
        flash("Access denied. Superadmin only.")
        return redirect(url_for("main.home"))

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    return render_template("superadmin_panel.html", users=users)


@main.route("/superadmin/update-role", methods=["POST"])
@login_required
def superadmin_update_role():
    if not _is_superadmin():
        flash("Access denied. Superadmin only.")
        return redirect(url_for("main.home"))

    email = request.form.get("email")
    role = request.form.get("role")

    if role not in ("admin", "user"):
        flash("Invalid role.")
        return redirect(url_for("main.superadmin_panel"))

    from .user_service import UserService

    user = UserService.get_user_by_email(email)
    if not user:
        flash("User not found.")
        return redirect(url_for("main.superadmin_panel"))

    _, _, user_email, _, user_role = user

    if user_role == "superadmin" and user_email != current_user.email:
        flash("Cannot change another superadmin.")
        return redirect(url_for("main.superadmin_panel"))

    if user_email == current_user.email and role != "superadmin":
        flash("You cannot remove your own superadmin role.")
        return redirect(url_for("main.superadmin_panel"))

    UserService.update_role_by_email(email, role)
    flash("Role updated.")
    return redirect(url_for("main.superadmin_panel"))


# ================= FAVORITES =================
@main.route("/favorites")
@login_required
def favorites():
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT anime_id FROM favorites WHERE user_id=?", (current_user.id,))
    anime_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not anime_ids:
        return render_template("index.html", page_mode="favorites", favorites=[])

    conn2 = sqlite3.connect(ANIME_DB_PATH)
    conn2.row_factory = sqlite3.Row
    cursor2 = conn2.cursor()
    query = f"SELECT * FROM anime WHERE anime_id IN ({','.join(['?'] * len(anime_ids))})"
    cursor2.execute(query, anime_ids)
    favorite_list = cursor2.fetchall()
    conn2.close()

    return render_template("index.html", page_mode="favorites", favorites=favorite_list)


# ================= WATCHLIST =================
@main.route("/watchlist")
@login_required
def watchlist():
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT anime_id FROM watchlist WHERE user_id=?", (current_user.id,))
    anime_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not anime_ids:
        return render_template("index.html", page_mode="watchlist", watchlist=[])

    conn2 = sqlite3.connect(ANIME_DB_PATH)
    conn2.row_factory = sqlite3.Row
    cursor2 = conn2.cursor()
    query = f"SELECT * FROM anime WHERE anime_id IN ({','.join(['?'] * len(anime_ids))})"
    cursor2.execute(query, anime_ids)
    watchlist_data = cursor2.fetchall()
    conn2.close()

    return render_template("index.html", page_mode="watchlist", watchlist=watchlist_data)


# ================= ADD FAVORITE =================
@main.route("/add_favorite/<int:anime_id>")
@login_required
def add_favorite(anime_id):
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM favorites WHERE user_id=? AND anime_id=?", (current_user.id, anime_id))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        message = "Already in Favorites"
        if _is_ajax_request():
            return jsonify({"ok": True, "message": message})
        flash(message)
        return redirect(request.referrer or url_for("main.home"))

    cursor.execute("INSERT INTO favorites (user_id, anime_id) VALUES (?, ?)", (current_user.id, anime_id))
    conn.commit()
    conn.close()

    message = "Added to Favorites"
    if _is_ajax_request():
        return jsonify({"ok": True, "message": message})
    flash(message)
    return redirect(request.referrer or url_for("main.home"))


# ================= REMOVE FAVORITE =================
@main.route("/remove_favorite/<int:anime_id>")
@login_required
def remove_favorite(anime_id):
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE user_id=? AND anime_id=?", (current_user.id, anime_id))
    conn.commit()
    conn.close()

    message = "Removed from Favorites"
    if _is_ajax_request():
        return jsonify({"ok": True, "message": message, "anime_id": anime_id})
    flash(message)
    return redirect(request.referrer or url_for("main.favorites"))


# ================= TOP RANKINGS =================
@main.route("/top-rankings")
@login_required
def top_rankings():
    page = request.args.get("page", 1, type=int)
    genre = request.args.get("genre")
    per_page = 10
    offset = (page - 1) * per_page

    conn = sqlite3.connect(ANIME_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if genre:
        cursor.execute(
            """
            SELECT * FROM anime
            WHERE genres LIKE ? AND score IS NOT NULL
            ORDER BY score DESC
            LIMIT ? OFFSET ?
            """,
            (f"%{genre}%", per_page, offset),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM anime
            WHERE score IS NOT NULL
            ORDER BY score DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        )

    rankings = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM anime WHERE score IS NOT NULL")
    total = cursor.fetchone()[0]
    conn.close()

    total_pages = math.ceil(total / per_page) if total else 1
    return render_template("index.html", page_mode="rankings", rankings=rankings, page=page, total_pages=total_pages)


# ================= ADD WATCHLIST =================
@main.route("/add_watchlist/<int:anime_id>")
@login_required
def add_watchlist(anime_id):
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM watchlist WHERE user_id=? AND anime_id=?", (current_user.id, anime_id))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        message = "Already in Watchlist"
        if _is_ajax_request():
            return jsonify({"ok": True, "message": message})
        flash(message)
        return redirect(request.referrer or url_for("main.home"))

    cursor.execute("INSERT INTO watchlist (user_id, anime_id) VALUES (?, ?)", (current_user.id, anime_id))
    conn.commit()
    conn.close()

    message = "Added to Watchlist"
    if _is_ajax_request():
        return jsonify({"ok": True, "message": message})
    flash(message)
    return redirect(request.referrer or url_for("main.home"))


# ================= REMOVE WATCHLIST =================
@main.route("/remove_watchlist/<int:anime_id>")
@login_required
def remove_watchlist(anime_id):
    from .user_service import init_user_db
    init_user_db()

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE user_id=? AND anime_id=?", (current_user.id, anime_id))
    conn.commit()
    conn.close()

    message = "Removed from Watchlist"
    if _is_ajax_request():
        return jsonify({"ok": True, "message": message, "anime_id": anime_id})
    flash(message)
    return redirect(request.referrer or url_for("main.watchlist"))
