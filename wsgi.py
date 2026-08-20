"""
Production entry point for gunicorn.

We use the application factory pattern in app.py (create_app()), but
gunicorn's --factory flag isn't available on every version and shell-
quoting "app:create_app()" is fragile across hosts. The simplest, most
portable fix is this file: it just calls the factory once at import
time and exposes the result as a plain module-level `app` object,
which every version of gunicorn understands.
"""

from app import create_app

app = create_app()
