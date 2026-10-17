"""Database tables."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Term(Base):
    """An approved glossary entry: an English term and its isiXhosa equivalent."""

    __tablename__ = "terms"
    # The same English/isiXhosa pair can't be stored twice. One English word
    # can still have more than one isiXhosa term, as separate rows.
    __table_args__ = (UniqueConstraint("english_norm", "xhosa_norm"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    english: Mapped[str] = mapped_column(String(120))
    xhosa: Mapped[str] = mapped_column(String(160))
    # Lowercase, accent-free copies used for searching (see search.normalise)
    english_norm: Mapped[str] = mapped_column(String(120), index=True)
    xhosa_norm: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    definition: Mapped[str] = mapped_column(Text)
    definition_xh: Mapped[str | None] = mapped_column(Text)
    example_xh: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Suggestion(Base):
    """A term suggested by the public, waiting to be reviewed."""

    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    english: Mapped[str] = mapped_column(String(120))
    xhosa: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(40))
    definition: Mapped[str] = mapped_column(Text)
    example_xh: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    submitted_by: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Set when the suggestion is approved and becomes a term
    term_id: Mapped[int | None] = mapped_column(ForeignKey("terms.id"))
