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

    # --- Access gate --------------------------------------------------------
    # Shared secret required to reach the app at all, handed out as
    # https://<host>/?k=<ACCESS_CODE> (QR code at the event). Empty = gate off.
    ACCESS_CODE = os.environ.get("ACCESS_CODE", "")

    # --- Session cookie security ------------------------------------------
    # Set SESSION_COOKIE_SECURE=true in production (behind HTTPS) so the
    # session cookie is only ever sent over TLS. Kept false by default so the
    # app still works over plain HTTP in local development.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
