from scripts.seed import seed

CSV = """english,xhosa,category,definition,definition_xh,example_xh,source
mouse,xh-mouse,computing,A small hand-held pointing device.,,,
keyboard,,computing,A set of keys for typing.,,,
broken,xh-broken,not-a-category,Bad row.,,,
"""


def test_seed_loads_translated_rows_only(client, tmp_path):
    path = tmp_path / "terms.csv"
    path.write_text(CSV, encoding="utf-8")

    first = seed(path)
    assert first == {"added": 1, "already_there": 0, "not_translated": 1, "invalid": 1}
    assert client.get("/api/terms").json()["total"] == 1

    # Running it again doesn't add duplicates
    again = seed(path)
    assert again["added"] == 0
    assert again["already_there"] == 1


def test_seed_reads_csv_saved_by_excel(client, tmp_path):
    # Excel's "CSV UTF-8" adds a byte-order mark and uses Windows line endings
    path = tmp_path / "terms.csv"
    path.write_bytes(b"\xef\xbb\xbf" + CSV.replace("\n", "\r\n").encode("utf-8"))
    assert seed(path)["added"] == 1


def test_real_csv_is_valid():
    """Every row in data/terms.csv has an English term, a known category and a definition."""
    import csv
    from pathlib import Path
    from app.config import CATEGORIES

    path = Path(__file__).resolve().parent.parent / "data" / "terms.csv"
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for row in rows:
        assert row["english"].strip()
        assert row["category"] in CATEGORIES
        assert len(row["definition"].strip()) >= 10
