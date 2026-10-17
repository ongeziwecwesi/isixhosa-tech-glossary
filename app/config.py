"""Settings read from environment variables, with defaults for local use."""

import os


def database_url() -> str:
    """
    SQLite file in the project folder by default. In production, set
    DATABASE_URL to a PostgreSQL connection string.

    Hosts like Neon give URLs starting with "postgres://" or "postgresql://".
    SQLAlchemy needs to be told which driver to use, so we rewrite the start
    to "postgresql+psycopg://" (psycopg 3).
    """
    url = os.getenv("DATABASE_URL", "sqlite:///./glossary.db")
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


DATABASE_URL = database_url()

# Key needed to review suggestions. If it isn't set, the admin endpoints
# are switched off rather than left open.
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")

# The categories a term can belong to.
CATEGORIES = [
    "computing",
    "programming",
    "internet",
    "networking",
    "data",
    "security",
]
