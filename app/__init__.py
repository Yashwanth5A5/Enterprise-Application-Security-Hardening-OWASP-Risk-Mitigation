"""
Enterprise Employee Management Portal
Application Factory
"""

import os
from flask import Flask
from .models.database import db, init_db


def create_app(config_name=None):
    """
    Application factory pattern for creating Flask app instances.
    Allows different configurations for development, testing, production.
    """
    app = Flask(__name__, instance_relative_config=True)

    # -------------------------------------------------------------------------
    # Base Configuration
    # -------------------------------------------------------------------------
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION"),
        DATABASE=os.path.join(app.instance_path, "emp_portal.db"),
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "emp_portal.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB max file size
        ALLOWED_EXTENSIONS={"pdf", "png", "jpg", "jpeg", "doc", "docx"},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # Load instance config if it exists (overrides defaults)
    if config_name == "testing":
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            WTF_CSRF_ENABLED=False,
        )

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # -------------------------------------------------------------------------
    # Initialize Extensions
    # -------------------------------------------------------------------------
    db.init_app(app)

    # -------------------------------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------------------------------
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.employees import employees_bp
    from .routes.files import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(files_bp)

    # -------------------------------------------------------------------------
    # Initialize Database and Seed Data
    # -------------------------------------------------------------------------
    with app.app_context():
        init_db(app)

    # -------------------------------------------------------------------------
    # Register Error Handlers
    # -------------------------------------------------------------------------
    from .routes.errors import register_error_handlers
    register_error_handlers(app)

    return app
