"""API tests. Clerk verification is mocked (no live Clerk calls) - it's
tested against real Clerk separately as a smoke test, same split as the
LLM client: mocked unit tests here, one live check outside the suite.
DB-touching tests run against real Neon with the same rollback-per-test
fixture used in test_db_models.py, via a dependency override.
"""

import uuid

import pytest
from clerk_backend_api.security.types import AuthStatus, RequestState
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.api.deps as deps
from app.db.models import Base, User
from app.db.session import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[deps.get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def _signed_in(clerk_user_id: str):
    return RequestState(status=AuthStatus.SIGNED_IN, payload={"sub": clerk_user_id})


def _signed_out():
    return RequestState(status=AuthStatus.SIGNED_OUT, reason=None)


def test_health_needs_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_me_without_token_is_rejected(client, monkeypatch):
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: _signed_out())

    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_valid_token_creates_and_returns_user(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: _signed_in(clerk_id))

    response = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"})
    assert response.status_code == 200
    body = response.json()
    assert body["clerk_user_id"] == clerk_id

    stored = db_session.query(User).filter_by(clerk_user_id=clerk_id).one()
    assert str(stored.id) == body["user_id"]


def test_me_reuses_existing_user_on_second_call(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: _signed_in(clerk_id))

    first = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"}).json()
    second = client.get("/api/me", headers={"Authorization": "Bearer fake-for-test"}).json()

    assert first["user_id"] == second["user_id"]
    assert db_session.query(User).filter_by(clerk_user_id=clerk_id).count() == 1
