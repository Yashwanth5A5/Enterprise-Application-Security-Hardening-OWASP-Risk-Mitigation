"""
Error Handlers
Custom HTTP error pages for 403, 404, and 500 responses.
"""

from flask import render_template, Blueprint

errors_bp = Blueprint("errors", __name__)


def register_error_handlers(app):
    """Register all custom error handlers with the Flask app."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500
