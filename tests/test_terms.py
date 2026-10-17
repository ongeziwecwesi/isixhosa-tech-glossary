from app.search import escape_like, normalise

# The isiXhosa values in these tests are placeholders for testing the code,
# not real translations.


def search(client, **params):
    res = client.get("/api/terms", params=params)
    assert res.status_code == 200
    return res.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_website_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "isiXhosa Tech Glossary" in res.text


def test_empty_glossary(client):
    page = search(client)
    assert page["total"] == 0
    assert page["items"] == []


def test_ranking_exact_then_prefix_then_contains(client, add_term):
    add_term("social network", "xh-a")
    add_term("network card", "xh-b")
    add_term("network", "xh-c")
    names = [t["english"] for t in search(client, q="network")["items"]]
    assert names == ["network", "network card", "social network"]


def test_search_matches_isixhosa(client, add_term):
    add_term("computer", "ikhompyutha-test")
    items = search(client, q="KHOMPYUTHA")["items"]
    assert [t["english"] for t in items] == ["computer"]


def test_search_ignores_case_and_extra_spaces(client, add_term):
    add_term("operating system", "xh-os")
    assert search(client, q="  Operating   SYSTEM ")["total"] == 1


def test_percent_sign_is_not_a_wildcard(client, add_term):
    add_term("network", "xh-net")
    assert search(client, q="%")["total"] == 0


def test_category_filter(client, add_term):
    add_term("virus", "xh-v", category="security")
    add_term("loop", "xh-l", category="programming")
    items = search(client, category="security")["items"]
    assert [t["english"] for t in items] == ["virus"]


def test_pagination(client, add_term):
    for i in range(25):
        add_term(f"term {i:02d}", f"xh {i:02d}")
    first = search(client, limit=10, offset=0)
    last = search(client, limit=10, offset=20)
    assert first["total"] == 25
    assert len(first["items"]) == 10
    assert len(last["items"]) == 5


def test_limits_are_validated(client):
    assert client.get("/api/terms", params={"limit": 500}).status_code == 422
    assert client.get("/api/terms", params={"q": "x" * 101}).status_code == 422


def test_get_term(client, add_term):
    term_id = add_term("mouse", "xh-m")
    assert client.get(f"/api/terms/{term_id}").json()["english"] == "mouse"
    assert client.get("/api/terms/9999").status_code == 404


def test_categories_include_empty_ones(client, add_term):
    add_term("virus", "xh-v", category="security")
    counts = {c["name"]: c["count"] for c in client.get("/api/categories").json()}
    assert counts["security"] == 1
    assert counts["networking"] == 0


def test_normalise():
    assert normalise("  Café   Wi-Fi ") == "cafe wi-fi"


def test_escape_like():
    assert escape_like("50%_off") == "50\\%\\_off"
