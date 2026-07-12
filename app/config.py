import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Application configuration.

    Override any value via environment variables. Sensible defaults are used
    so the app runs out-of-the-box for local/single-machine use.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Single local SQLite file — the whole database lives in ducktails.db
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'ducktails.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Default admin account created on first seed. Change the password after
    # first login (or set these env vars before seeding).
    DEFAULT_ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
