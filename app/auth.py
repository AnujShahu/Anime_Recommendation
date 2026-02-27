from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
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


@auth.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    success, message = UserService.create_user(username, email, password)
    flash(message)

    # Always redirect back to home (modal system)
    return redirect(url_for("main.home"))


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
        flash("Invalid credentials!")

    # Always return to homepage (modal UI)
    return redirect(url_for("main.home"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You are now browsing as Guest.")
    return redirect(url_for("main.home"))