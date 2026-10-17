"""Text normalisation and search for glossary terms."""

import re
import unicodedata

from sqlalchemy import case, func, or_, select

from app.models import Term


def normalise(text: str) -> str:
    """
    Turn text into the form we store and search on.

    "  Ikhompyutha " -> "ikhompyutha"
    "Café"           -> "cafe"

    Lowercase, accents removed, and repeated spaces collapsed, so a search
    matches no matter how the person typed it.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def escape_like(text: str) -> str:
    """
    Escape the characters LIKE treats as wildcards.

    Without this, a search for "100%" would match everything starting
    with "100", because % means "anything" in SQL.
    """
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_search_query(q: str | None, category: str | None):
    """
    Build the query for /api/terms.

    Matches the search text in either English or isiXhosa, and ranks:
      0  exact match           ("network")
      1  starts with the text  ("network" -> "network card")
      2  contains the text     ("work"    -> "network")
    Ties are broken alphabetically by the English term.
    """
    stmt = select(Term)

    if category:
        stmt = stmt.where(Term.category == category)

    if not q or not normalise(q):
        return stmt.order_by(Term.english_norm)

    q_norm = escape_like(normalise(q))
    starts = f"{q_norm}%"
    contains = f"%{q_norm}%"

    rank = case(
        (or_(Term.english_norm == normalise(q), Term.xhosa_norm == normalise(q)), 0),
        (or_(Term.english_norm.like(starts, escape="\\"),
             Term.xhosa_norm.like(starts, escape="\\")), 1),
        else_=2,
    )

    return (
        stmt.where(or_(Term.english_norm.like(contains, escape="\\"),
                       Term.xhosa_norm.like(contains, escape="\\")))
            .order_by(rank, func.length(Term.english_norm), Term.english_norm)
    )
