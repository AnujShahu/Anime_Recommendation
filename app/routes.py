from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .recommender import get_recommendations, get_anime_by_genre
from .user_service import UserService

main = Blueprint("main", __name__)


# ================= HOME =================
@main.route("/")
def home():
    return render_template("index.html")


# ================= RECOMMENDATION =================
@main.route("/recommend", methods=["POST"])
def recommend():
    anime_name = request.form.get("anime_name")

    if not anime_name:
        flash("Please enter an anime name!")
        return redirect(url_for("main.home"))

    recommendations = get_recommendations(anime_name)

    if not recommendations:
        flash("No recommendations found.")
        return redirect(url_for("main.home"))

    return render_template(
        "index.html",
        recommendations=recommendations,
        searched_anime=anime_name
    )


# ================= BROWSE BY GENRE =================
@main.route("/genre/<genre>")
def browse_genre(genre):
    page = request.args.get("page", 1, type=int)
    per_page = 12

    anime_list = get_anime_by_genre(genre)

    if not anime_list:
        flash("No anime found for this genre.")
        return redirect(url_for("main.home"))

    total = len(anime_list)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_anime = anime_list[start:end]
    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "index.html",
        genre=genre,
        genre_anime=paginated_anime,
        page=page,
        total_pages=total_pages
    )


# ================= ADMIN DASHBOARD =================
@main.route("/admin")
@login_required
def admin_dashboard():

    # Protect admin route
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("main.home"))

    # Get all users
    import sqlite3
    from .user_service import USER_DB_PATH

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, role FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template("admin_dashboard.html", users=users)


# ================= PROMOTE USER =================
@main.route("/promote/<int:user_id>")
@login_required
def promote_user(user_id):

    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("main.home"))

    import sqlite3
    from .user_service import USER_DB_PATH

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET role='admin' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    flash("User promoted to admin.")
    return redirect(url_for("main.admin_dashboard"))


# ================= DEMOTE USER =================
@main.route("/demote/<int:user_id>")
@login_required
def demote_user(user_id):

    if not current_user.is_admin:
        flash("Access denied.")
        return redirect(url_for("main.home"))

    import sqlite3
    from .user_service import USER_DB_PATH

    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET role='user' WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    flash("User demoted to normal user.")
    return redirect(url_for("main.admin_dashboard"))