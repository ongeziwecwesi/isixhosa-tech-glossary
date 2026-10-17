import pytest

VALID = {
    "english": "cloud",
    "xhosa": "xh-cloud",
    "category": "internet",
    "definition": "Computers on the internet that store your files and run programs.",
    "submitted_by": "Test User",
}


def suggest(client, **changes):
    return client.post("/api/suggestions", json={**VALID, **changes})


# ── Suggesting ───────────────────────────────────────────────────────────────

def test_create_suggestion(client):
    res = suggest(client)
    assert res.status_code == 201
    assert res.json()["status"] == "pending"


@pytest.mark.parametrize("changes", [
    {"category": "cooking"},
    {"definition": "short"},
    {"english": "   "},
    {"xhosa": ""},
])
def test_invalid_suggestions_are_rejected(client, changes):
    assert suggest(client, **changes).status_code == 422


def test_cannot_suggest_existing_term(client, add_term):
    add_term("cloud", "xh-cloud")
    assert suggest(client, english="Cloud").status_code == 409


def test_cannot_suggest_same_pending_term_twice(client):
    assert suggest(client).status_code == 201
    assert suggest(client, english="CLOUD ").status_code == 409


def test_suggestion_does_not_appear_until_approved(client):
    suggest(client)
    assert client.get("/api/terms", params={"q": "cloud"}).json()["total"] == 0


# ── Reviewing ────────────────────────────────────────────────────────────────

def test_review_is_off_without_a_key(client):
    assert client.get("/api/suggestions").status_code == 503


def test_review_needs_the_right_key(client, admin):
    assert client.get("/api/suggestions").status_code == 401
    assert client.get("/api/suggestions", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/api/suggestions", headers=admin).status_code == 200


def test_list_pending(client, admin):
    suggest(client)
    pending = client.get("/api/suggestions", headers=admin).json()
    assert [s["english"] for s in pending] == ["cloud"]


def test_approve_adds_the_term(client, admin):
    sid = suggest(client).json()["id"]
    res = client.post(f"/api/suggestions/{sid}/approve", headers=admin,
                      json={"review_note": "Checked"})
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    found = client.get("/api/terms", params={"q": "cloud"}).json()["items"]
    assert len(found) == 1
    assert found[0]["source"] == "Suggested by Test User"
    assert found[0]["id"] == res.json()["term_id"]


def test_cannot_approve_twice(client, admin):
    sid = suggest(client).json()["id"]
    client.post(f"/api/suggestions/{sid}/approve", headers=admin)
    assert client.post(f"/api/suggestions/{sid}/approve", headers=admin).status_code == 409


def test_reject(client, admin):
    sid = suggest(client).json()["id"]
    res = client.post(f"/api/suggestions/{sid}/reject", headers=admin,
                      json={"review_note": "Not the usual term"})
    assert res.json()["status"] == "rejected"
    assert client.get("/api/terms", params={"q": "cloud"}).json()["total"] == 0
    rejected = client.get("/api/suggestions", params={"status": "rejected"}, headers=admin).json()
    assert len(rejected) == 1


def test_review_unknown_suggestion(client, admin):
    assert client.post("/api/suggestions/999/approve", headers=admin).status_code == 404
