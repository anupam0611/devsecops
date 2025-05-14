"""
Authentication module.

This module handles user authentication, including login, registration,
password reset, and account management.
"""

# Standard library imports
import smtplib

# Third-party imports
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from models import User
from utils.security import log_security_event

# Create auth blueprint
auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember", False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            log_security_event("login", f"User {user.id} logged in", user.id)
            flash("Logged in successfully.", "success")
            return redirect(url_for("main.index"))

        log_security_event("login_failed", f"Failed login attempt for {email}")
        flash(
            "Invalid email or password. Please try again.",
            "error",
        )

    return render_template("auth/login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash(
                "Passwords do not match. Please enter the same password in both fields.",
                "error",
            )
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash(
                "Email already registered. Please use a different email address.",
                "error",
            )
            return render_template("auth/register.html")

        try:
            user = User(email=email)
            user.set_password(password)
            current_app.db.session.add(user)
            current_app.db.session.commit()

            log_security_event("registration", f"New user registered: {email}", user.id)
            flash(
                "Registration successful. Please log in to access your account.",
                "success",
            )
            return redirect(url_for("auth.login"))

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(
                f"Database error during registration: {str(e)}"
            )
            flash("An error occurred during registration.", "error")

    return render_template("auth/register.html")


@auth.route("/logout")
@login_required
def logout():
    """Handle user logout."""
    log_security_event(
        "logout",
        f"User {current_user.id} logged out",
        current_user.id,
    )

    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("main.index"))


@auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.generate_reset_token()
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            try:
                current_app.mail.send_message(
                    "Password Reset Request",
                    recipients=[user.email],
                    body=(
                        f"To reset your password, visit the following link:\n"
                        f"{reset_url}"
                    ),
                )
                log_security_event(
                    "password_reset_request",
                    f"Reset requested for {email}",
                    user.id,
                )
                flash(
                    "Password reset instructions sent to your email address.",
                    "info",
                )
                return redirect(url_for("auth.login"))

            except smtplib.SMTPException as e:
                current_app.logger.error(
                    f"SMTP error while sending reset email: {str(e)}"
                )
                flash(
                    "Error sending reset email. Please try again.",
                    "error",
                )
        else:
            flash("Email not found.", "error")

    return render_template("auth/reset_password_request.html")


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    user = User.verify_reset_token(token)
    if not user:
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for("auth.reset_password_request"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/reset_password.html")

        try:
            user.set_password(password)
            current_app.db.session.commit()
            log_security_event(
                "password_reset",
                f"Password reset for {user.email}",
                user.id,
            )
            flash(
                "Your password has been reset successfully. You can now log in.",
                "success",
            )
            return redirect(url_for("auth.login"))

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(
                f"Database error during password reset: {str(e)}"
            )
            flash("An error occurred during password reset.", "error")

    return render_template("auth/reset_password.html")
