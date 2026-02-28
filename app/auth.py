from flask import Blueprint, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
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

    success, message = UserService.create_user(username, email, password)
    flash(message)
    return redirect(url_for("main.home"))


# ================= LOGIN =================
@auth.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")

    user_data = UserService.authenticate_user(email, password)

    if user_data:
        user_obj = User(*user_data)
        login_user(user_obj)
        flash("Logged in successfully!")
    else:
        flash("Invalid email or password!")

    return redirect(url_for("main.home"))


# ================= LOGOUT =================
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("main.home"))


# ================= FORGOT PASSWORD =================
def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset")


def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        email = serializer.loads(token, salt="password-reset", max_age=expiration)
        return email
    except:
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
        UserService.update_password(email, new_password)
        flash("Password updated successfully!")
        return redirect(url_for("main.home"))

    return """
    <form method="POST">
        <input type="password" name="password" placeholder="New Password" required>
        <button type="submit">Reset</button>
    </form>
    """