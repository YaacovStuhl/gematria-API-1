from __future__ import annotations

from flask import abort
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError

from .extensions import db
from .models import GematriaEntry
from .schemas import (
    EntryCreateSchema,
    EntrySchema,
    EntryUpdateSchema,
    EntryUpsertByPhraseSchema,
    GematriaLookupResponseSchema,
    GematriaQueryArgsSchema,
    MatchesQueryArgsSchema,
)

from flask_smorest import Blueprint


blp = Blueprint("gematria", __name__, url_prefix="/", description="Gematria endpoints")


@blp.route("/gematria")
class GematriaLookup(MethodView):
    @blp.arguments(GematriaQueryArgsSchema, location="query")
    @blp.response(200, GematriaLookupResponseSchema)
    def get(self, args):
        phrase = args["phrase"].strip()
        try:
            entry = db.session.execute(
                db.select(GematriaEntry).where(GematriaEntry.phrase == phrase)
            ).scalar_one_or_none()
        except OperationalError:
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")

        if entry is None:
            abort(404, description="Phrase not found")

        return {"phrase": entry.phrase, "value": entry.value, "found": True}


@blp.route("/matches")
class Matches(MethodView):
    @blp.arguments(MatchesQueryArgsSchema, location="query")
    @blp.response(200, EntrySchema(many=True))
    def get(self, args):
        value = args["value"]
        top = args["top"]

        try:
            # Uses the DB index on public.gematria_entries.value.
            entries = (
                db.session.execute(
                    db.select(GematriaEntry)
                    .where(GematriaEntry.value == value)
                    .order_by(GematriaEntry.phrase.asc())
                    .limit(top)
                )
                .scalars()
                .all()
            )
        except OperationalError:
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")

        return [
            {"id": e.id, "phrase": e.phrase, "value": e.value, "source": None}
            for e in entries
        ]


@blp.route("/entries")
class Entries(MethodView):
    @blp.arguments(EntryCreateSchema)
    @blp.response(201, EntrySchema)
    def post(self, payload):
        phrase = payload["phrase"].strip()
        value = payload["value"]

        entry = GematriaEntry(phrase=phrase, value=value)

        db.session.add(entry)
        try:
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            db.session.rollback()
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")
        except IntegrityError:
            db.session.rollback()
            abort(409, description="Phrase already exists")

        return {"id": entry.id, "phrase": entry.phrase, "value": entry.value, "source": None}


@blp.route("/entries/<int:entry_id>")
class EntryById(MethodView):
    @blp.arguments(EntryUpdateSchema)
    @blp.response(200, EntrySchema)
    def put(self, payload, entry_id: int):
        try:
            entry = db.session.get(GematriaEntry, entry_id)
        except OperationalError:
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")
        if entry is None:
            abort(404, description="Entry not found")

        if payload.get("phrase") is not None:
            entry.phrase = payload["phrase"].strip()
        if payload.get("value") is not None:
            entry.value = payload["value"]

        try:
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            db.session.rollback()
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")
        except IntegrityError:
            db.session.rollback()
            abort(409, description="Phrase already exists")

        return {"id": entry.id, "phrase": entry.phrase, "value": entry.value, "source": None}

    @blp.response(200, EntrySchema)
    def delete(self, entry_id: int):
        """
        Delete an entry by id.
        """
        try:
            entry = db.session.get(GematriaEntry, entry_id)
        except OperationalError:
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")

        if entry is None:
            abort(404, description="Entry not found")

        deleted = {"id": entry.id, "phrase": entry.phrase, "value": entry.value, "source": None}
        db.session.delete(entry)
        try:
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            db.session.rollback()
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")

        return deleted


@blp.route("/entries/by-phrase")
class EntryByPhrase(MethodView):
    """
    Convenience endpoint for bulk loaders: upsert by unique phrase (no ID needed).
    """

    @blp.arguments(EntryUpsertByPhraseSchema)
    @blp.response(200, EntrySchema)
    def put(self, payload):
        phrase = payload["phrase"].strip()
        value = payload["value"]

        try:
            entry = db.session.execute(
                db.select(GematriaEntry).where(GematriaEntry.phrase == phrase)
            ).scalar_one_or_none()
        except OperationalError:
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")

        if entry is None:
            entry = GematriaEntry(phrase=phrase, value=value)
            db.session.add(entry)
        else:
            entry.value = value

        try:
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            abort(503, description="Database connection failed. Check DATABASE_URL.")
        except ProgrammingError:
            db.session.rollback()
            abort(503, description="Database schema missing. Ensure public.gematria_entries exists (restore/migrate).")
        except IntegrityError:
            db.session.rollback()
            abort(409, description="Phrase already exists")

        return {"id": entry.id, "phrase": entry.phrase, "value": entry.value, "source": None}


