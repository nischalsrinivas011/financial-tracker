"""API tests. Clerk verification is mocked (no live Clerk calls) - it's
tested against real Clerk separately as a smoke test, same split as the
LLM client: mocked unit tests here, one live check outside the suite.
"""

import uuid

import app.api.deps as deps
from app.db.models import User
from tests.helpers import signed_in, signed_out


def test_health_needs_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_without_token_is_rejected(client, monkeypatch):
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_out())

    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_valid_token_creates_and_returns_user(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_in(clerk_id))

    response = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"})
    assert response.status_code == 200
    body = response.json()
    assert body["clerk_user_id"] == clerk_id

    stored = db_session.query(User).filter_by(clerk_user_id=clerk_id).one()
    assert str(stored.id) == body["user_id"]


def test_me_reuses_existing_user_on_second_call(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_in(clerk_id))

    first = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"}).json()
    second = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"}).json()

    assert first["user_id"] == second["user_id"]
    assert db_session.query(User).filter_by(clerk_user_id=clerk_id).count() == 1
