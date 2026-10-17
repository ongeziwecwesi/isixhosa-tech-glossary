import pytest

from app.config import database_url


@pytest.mark.parametrize("given, expected", [
    ("postgres://u:p@host/db?sslmode=require", "postgresql+psycopg://u:p@host/db?sslmode=require"),
    ("postgresql://u:p@host/db", "postgresql+psycopg://u:p@host/db"),
    ("sqlite:///./glossary.db", "sqlite:///./glossary.db"),
])
def test_database_url_picks_the_psycopg_driver(monkeypatch, given, expected):
    monkeypatch.setenv("DATABASE_URL", given)
    assert database_url() == expected


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert database_url().startswith("sqlite")
