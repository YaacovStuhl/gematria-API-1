"""Application package (Flask app and shared helpers live here)."""

from __future__ import annotations

from flask import Flask, abort, current_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import api, db
from .routes import blp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    api.init_app(app)

    api.register_blueprint(blp)

    @app.get("/")
    def index():
        return {
            "service": "Gematria API",
            "swagger_ui": "/swagger-ui",
            "openapi_json": "/openapi.json",
            "endpoints": ["/gematria", "/matches", "/entries", "/entries/{id}", "/entries/by-phrase"],
        }

    # Local-only helper for diagnosing "wrong DB" issues.
    # Hidden in production: returns 404 unless Flask is running in debug mode.
    @app.get("/debug/db")
    def debug_db():
        if not current_app.debug:
            abort(404)
        try:
            info = db.session.execute(
                text(
                    """
                    SELECT
                      current_database() AS database,
                      current_user AS user
                    """
                )
            ).mappings().one()
            count = db.session.execute(
                text("SELECT COUNT(*) AS n FROM public.gematria_entries")
            ).mappings().one()["n"]
        except OperationalError as e:
            return {"ok": False, "error": str(e)}, 503

        return {"ok": True, "database": info["database"], "user": info["user"], "entries_count": int(count)}

    if app.config.get("AUTO_CREATE_TABLES", False):
        with app.app_context():
            db.create_all()

    return app



