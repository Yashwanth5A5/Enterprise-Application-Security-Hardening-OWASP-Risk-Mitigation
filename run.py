"""
Application Entry Point
Run with: python run.py
Or with Flask CLI: flask run
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,  # NOTE: Set debug=False in production
    )
