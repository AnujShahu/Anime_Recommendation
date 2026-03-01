from flask import Blueprint, request, redirect, url_for, flash, current_app, render_template
from flask_login import login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import check_password_hash
from .models import User
from . import login_manager
from .user_service import UserService

auth = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    user_data = UserService.get_user_by_id(user_id)
    if user_data:
        return User(*user_data)
    return None


# ================= REGISTER =================
@auth.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not email or not password:
        flash("All fields are required!")
        return redirect(url_for("main.home"))

    success, message = UserService.create_user(username, email, password)

    flash(message)
    return redirect(url_for("main.home"))


# ================= LOGIN =================
@auth.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    if not email or not password:
        flash("Email and password required!")
        return redirect(url_for("main.home"))

    user_data = UserService.get_user_by_email(email)

    if not user_data:
        flash("Invalid username/password")
        return redirect(url_for("main.home"))

    user = User(*user_data)

    if not check_password_hash(user.password, password):
        flash("Invalid username/password")
        return redirect(url_for("main.home"))

    login_user(user)
    flash("Login successful!")
    return redirect(url_for("main.home"))


# ================= LOGOUT =================
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("main.home"))


# ================= RESET TOKEN =================
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset")


def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="password-reset", max_age=expiration)
    except Exception:
        return None


@auth.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email")
    user = UserService.get_user_by_email(email)

    if user:
        token = generate_reset_token(email)
        reset_link = url_for("auth.reset_password", token=token, _external=True)
        flash(f"Reset link (valid 1 hour): {reset_link}")
    else:
        flash("Email not found!")

    return redirect(url_for("main.home"))


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)

    if not email:
        flash("Invalid or expired token.")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        new_password = request.form.get("password")

        if not new_password:
            flash("Password required!")
            return redirect(url_for("main.home"))

        UserService.update_password(email, new_password)
        flash("Password updated successfully!")
        return redirect(url_for("main.home"))

    return render_template("reset_password.html", token=token)