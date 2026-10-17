"""
Load terms from data/terms.csv into the database.

    python scripts/seed.py

Rows with an empty isiXhosa column are skipped, so the CSV can hold terms
that haven't been translated yet. Running the script again is safe: terms
already in the database are left alone.
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.config import CATEGORIES  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Term  # noqa: E402
from app.search import normalise  # noqa: E402

CSV_PATH = ROOT / "data" / "terms.csv"


def clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def seed(csv_path: Path = CSV_PATH) -> dict:
    Base.metadata.create_all(bind=engine)
    counts = {"added": 0, "already_there": 0, "not_translated": 0, "invalid": 0}

    with open(csv_path, encoding="utf-8-sig", newline="") as f, SessionLocal() as db:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            english, xhosa = clean(row["english"]), clean(row["xhosa"])
            category, definition = clean(row["category"]), clean(row["definition"])

            if english and not xhosa:
                counts["not_translated"] += 1
                continue
            if not (english and category in CATEGORIES and definition):
                print(f"  line {line_no}: skipped, missing or invalid field")
                counts["invalid"] += 1
                continue

            exists = db.scalar(select(Term).where(
                Term.english_norm == normalise(english),
                Term.xhosa_norm == normalise(xhosa),
            ))
            if exists:
                counts["already_there"] += 1
                continue

            db.add(Term(
                english=english,
                xhosa=xhosa,
                english_norm=normalise(english),
                xhosa_norm=normalise(xhosa),
                category=category,
                definition=definition,
                definition_xh=clean(row.get("definition_xh")),
                example_xh=clean(row.get("example_xh")),
                source=clean(row.get("source")),
            ))
            counts["added"] += 1
        db.commit()

    return counts


if __name__ == "__main__":
    result = seed()
    print(f"Added {result['added']} terms, {result['already_there']} already there, "
          f"{result['not_translated']} still need an isiXhosa translation, "
          f"{result['invalid']} invalid.")
