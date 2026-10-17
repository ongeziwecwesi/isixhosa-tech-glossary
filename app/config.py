"""Settings read from environment variables, with defaults for local use."""

import os

# SQLite file in the project folder by default. Point this at another
# database (e.g. PostgreSQL) in production.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./glossary.db")

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
