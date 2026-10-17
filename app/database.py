"""Database connection and session handling."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

# SQLite only allows a connection to be used by the thread that created it.
# FastAPI may handle a request on a different thread, so we switch that check off.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping checks a connection still works before using it. Free
# Postgres hosts like Neon close idle connections, and without this the
# first request after a quiet spell would fail.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Give each request its own session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
