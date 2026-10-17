import os
import sys
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database BEFORE it is imported.
# SQLite by default; set TEST_DATABASE_URL to run the tests against Postgres.
TEST_DB = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{TEST_DB}")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import config  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Term  # noqa: E402
from app.search import normalise  # noqa: E402

ADMIN_KEY = "test-admin-key"


@pytest.fixture(autouse=True)
def fresh_db():
    """Every test starts with empty tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def admin(monkeypatch):
    """Switch reviewing on and return the headers an admin would send."""
    monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
    return {"X-Admin-Key": ADMIN_KEY}


@pytest.fixture()
def add_term():
    """Insert a term straight into the database."""
    def _add(english, xhosa, category="computing", definition="A test definition."):
        with SessionLocal() as db:
            term = Term(english=english, xhosa=xhosa,
                        english_norm=normalise(english), xhosa_norm=normalise(xhosa),
                        category=category, definition=definition)
            db.add(term)
            db.commit()
            return term.id
    return _add
