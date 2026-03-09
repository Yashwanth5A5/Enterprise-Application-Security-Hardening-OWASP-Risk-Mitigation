"""
Application Entry Point
Run with: python run.py
Or with Flask CLI: flask run
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") in ("1", "true", "True")
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=debug,  # NOTE: Do not enable debug in production
    )
