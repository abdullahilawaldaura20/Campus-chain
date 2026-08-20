from flask_sqlalchemy import SQLAlchemy

# Initialized here, bound to the app in app.py, so models.py and routes/*.py
# can all import `db` without creating circular imports.
db = SQLAlchemy()
