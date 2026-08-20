import os


class Config:
    """
    App configuration, pulled from environment variables so real
    credentials never get committed to source control.
    Copy .env.example to .env and fill in your own values for local dev.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Render (and most Postgres hosts) provide a single DATABASE_URL env var.
    # Fall back to building one from individual DB_* vars for local development.
    _database_url = os.environ.get("DATABASE_URL")

    if _database_url:
        # SQLAlchemy 1.4+/2.x requires the "postgresql://" scheme, but some
        # hosts (Render included) still hand out "postgres://" — normalize it.
        if _database_url.startswith("postgres://"):
            _database_url = _database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        DB_USER = os.environ.get("DB_USER", "postgres")
        DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
        DB_HOST = os.environ.get("DB_HOST", "localhost")
        DB_PORT = os.environ.get("DB_PORT", "5432")
        DB_NAME = os.environ.get("DB_NAME", "campuschain")
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Only students with this email domain can register.
    # Set to None to allow any email during local development.
    ALLOWED_EMAIL_DOMAIN = os.environ.get("ALLOWED_EMAIL_DOMAIN", None)
