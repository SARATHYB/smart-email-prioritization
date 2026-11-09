# tests/test_api.py
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_emails():
    # Trigger demo reset to ensure fresh state
    reset_resp = client.post("/api/ingest/reset-demo")
    assert reset_resp.status_code == 200

    response = client.get("/api/emails")
    assert response.status_code == 200
    emails = response.json()
    assert len(emails) > 0
    # Verify emails are sorted by tuds_score descending
    scores = [e["tuds_score"] for e in emails]
    assert scores == sorted(scores, reverse=True)


def test_recompute_priorities():
    payload = {
        "alpha": 2.5,
        "user_interest_weights": {
            "placement": 1.0,
            "internship": 0.8,
            "exam": 0.9,
            "scholarship": 0.7,
            "event": 0.5,
            "general": 0.3
        },
        "category_lambdas": {
            "placement": 0.08,
            "internship": 0.05,
            "exam": 0.09,
            "scholarship": 0.06,
            "event": 0.04,
            "general": 0.02
        }
    }
    response = client.post("/api/emails/recompute", json=payload)
    assert response.status_code == 200
    assert response.json()["updated_count"] > 0
