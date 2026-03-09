"""
Authentication Routes
Handles user login, logout, and session management.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models.database import db, User
from app.utils import log_action

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -----------------------------------------------------------------------------
# LOGIN
# -----------------------------------------------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    GET  /auth/login  – Render the login form.
    POST /auth/login  – Process credentials and establish session.
    """
    # Redirect already-authenticated users to dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic presence validation
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("auth/login.html")

        # Look up user
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            # Establish session
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["user_role"] = user.role

            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.session.commit()

            log_action("LOGIN", resource="auth", status="success")
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("dashboard.index"))
        else:
            log_action("LOGIN", resource="auth", status="failure",
                       details=f"Failed login attempt for username: {username}")
            flash("Invalid username or password.", "danger")

    return render_template("auth/login.html")


# -----------------------------------------------------------------------------
# LOGOUT
# -----------------------------------------------------------------------------
@auth_bp.route("/logout")
def logout():
    """
    GET /auth/logout – Clear session and redirect to login.
    """
    log_action("LOGOUT", resource="auth", status="success")
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# -----------------------------------------------------------------------------
# ROOT REDIRECT
# -----------------------------------------------------------------------------
@auth_bp.route("/")
def root():
    return redirect(url_for("auth.login"))
