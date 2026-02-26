from flask import Blueprint, render_template, request, redirect, url_for, flash
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

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        success, message = UserService.create_user(username, email, password)
        flash(message)

        if success:
            return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user_data = UserService.authenticate_user(email, password)

        if user_data:
            user_obj = User(*user_data)
            login_user(user_obj)
            flash("Logged in successfully!")
            return redirect(url_for("main.home"))

        flash("Invalid credentials!")

    return render_template("login.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You are now browsing as Guest.")
    return redirect(url_for("main.home"))