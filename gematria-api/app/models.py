from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


class GematriaEntry(db.Model):
    """
    Maps to the existing PostgreSQL table:
      public.gematria_entries(id PK, phrase TEXT UNIQUE, value INT INDEXED)
    """

    __tablename__ = "gematria_entries"
    __table_args__ = {"schema": "public"}

    id: Mapped[int] = mapped_column(primary_key=True)
    phrase: Mapped[str] = mapped_column(db.Text, unique=True, nullable=False)
    value: Mapped[int] = mapped_column(db.Integer, nullable=False)


