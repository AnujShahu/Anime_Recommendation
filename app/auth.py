from flask import Blueprint, request, redirect, url_for, flash, current_app, render_template, session
from flask_login import login_user, logout_user, login_required
from email.message import EmailMessage
import os
import secrets
import smtplib
import time
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


def _send_reset_code_email(to_email, code):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

    if not smtp_host or not smtp_user or not smtp_pass or not smtp_from:
        current_app.logger.warning("SMTP not configured; cannot send reset code email.")
        return False

    message = EmailMessage()
    message["Subject"] = "Your password reset code"
    message["From"] = smtp_from
    message["To"] = to_email
    message.set_content(
        f"Your password reset code is: {code}\n\n"
        "This code expires in 10 minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if use_tls:
                server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(message)
        return True
    except Exception:
        current_app.logger.exception("Failed to send reset code email.")
        return False


@auth.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email")
    user = UserService.get_user_by_email(email)

    if user:
        code = f"{secrets.randbelow(1000000):06d}"
        expires_at = int(time.time()) + 600
        UserService.create_password_reset(email, code, expires_at)

        if _send_reset_code_email(email, code):
            flash("Verification code sent to your email.")
            return redirect(url_for("auth.verify_code", email=email))
        flash("Email service not configured. Contact support.")
        return redirect(url_for("main.home"))

    flash("If the email exists, a code has been sent.")

    return redirect(url_for("main.home"))


@auth.route("/verify-code", methods=["GET", "POST"])
def verify_code():
    email = request.values.get("email")
    if not email:
        flash("Email required.")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        if not code.isdigit() or len(code) != 6:
            flash("Enter the six digit code.")
            return redirect(url_for("auth.verify_code", email=email))
        ok, message = UserService.verify_password_reset(email, code)
        if not ok:
            flash(message)
            return redirect(url_for("auth.verify_code", email=email))

        session["reset_email"] = email
        session["reset_verified_at"] = int(time.time())
        flash("Code verified. Set your new password.")
        return redirect(url_for("auth.reset_password"))

    return render_template("verify_code.html", email=email)


@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    verified_at = session.get("reset_verified_at")

    if not email or not verified_at:
        flash("Password reset session expired.")
        return redirect(url_for("main.home"))

    if int(time.time()) - int(verified_at) > 900:
        session.pop("reset_email", None)
        session.pop("reset_verified_at", None)
        flash("Password reset session expired.")
        return redirect(url_for("main.home"))

    if request.method == "POST":
        new_password = request.form.get("password")
        if not new_password:
            flash("Password required!")
            return redirect(url_for("auth.reset_password"))

        UserService.update_password(email, new_password)
        UserService.clear_password_reset(email)
        session.pop("reset_email", None)
        session.pop("reset_verified_at", None)
        flash("Password updated successfully!")
        return redirect(url_for("main.home"))

    return render_template("reset_password.html")
