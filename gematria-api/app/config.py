from __future__ import annotations

import os


def _normalize_database_url(url: str | None) -> str | None:
    """
    Render/Heroku sometimes provide postgres:// URLs; SQLAlchemy expects postgresql://.
    """
    if not url:
        return None
    if url.startswith("postgres://"):
        return "postgresql://" + url.removeprefix("postgres://")
    return url


class Config:
    API_TITLE = "Gematria API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prefer DATABASE_URL so you can swap local vs Render without code changes.
    # If DATABASE_URL is not set, fall back to your local dev connection string.
    _db_url = _normalize_database_url(os.getenv("DATABASE_URL")) or "postgresql://postgres:Chargers93@localhost:5432/gematria"
    SQLALCHEMY_DATABASE_URI = _db_url

    # Opt-in only: creating tables requires a working DB connection.
    # Set AUTO_CREATE_TABLES=true if you want SQLAlchemy to create any missing tables.
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "false").lower() in {"1", "true", "yes", "y", "on"}


