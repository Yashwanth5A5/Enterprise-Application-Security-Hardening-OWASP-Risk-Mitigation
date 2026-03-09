"""
Access Control Decorators and Helpers
Provides login_required and admin_required decorators for route protection.
NOTE: Phase 2 will demonstrate and harden these controls.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(f):
    """
    Decorator: Redirect to login page if the user is not authenticated.
    Protects routes that require a valid session.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator: Return 403 Forbidden if the current user is not an Admin.
    Protects admin-only routes such as delete operations.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("user_role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """
    Helper: Return the current authenticated User object from the session,
    or None if no user is logged in.
    """
    from app.models.database import User
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None


def log_action(action, resource=None, resource_id=None, status="success", details=None):
    """
    Helper: Write an entry to the AuditLog table.
    Called from route handlers to record significant events.
    """
    from flask import request
    from app.models.database import db, AuditLog

    log = AuditLog(
        user_id=session.get("user_id"),
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=request.remote_addr,
        status=status,
        details=details,
    )
    db.session.add(log)
    db.session.commit()
