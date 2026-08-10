import uuid
from datetime import date

import app.api.deps as deps
import app.rag.answer as answer_module
from app.db.models import Account, Statement, Transaction, User
from app.llm.client import LLMResponse
from tests.helpers import signed_in, signed_out


def _seed_user_with_transactions(db_session, clerk_user_id):
    user = User(clerk_user_id=clerk_user_id)
    db_session.add(user)
    db_session.flush()

    account = Account(
        user_id=user.id, kind="bank", institution="HDFC BANK", account_number_masked="XXXXXXXXXX1736",
    )
    db_session.add(account)
    db_session.flush()

    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0, reconciled=True,
    )
    db_session.add(statement)
    db_session.flush()

    db_session.add(Transaction(
        account_id=account.id, statement_id=statement.id, date=date(2026, 3, 5),
        narration="n1", merchant="ZOMATO", category="food_delivery", direction="debit", amount_paise=30000,
    ))
    db_session.flush()
    return user


def _authed(client, monkeypatch, clerk_id: str):
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_in(clerk_id))


def test_ask_requires_auth(client, monkeypatch):
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_out())
    response = client.post("/ask", json={"question": "What is the 50/30/20 rule?"})
    assert response.status_code == 401


def test_ask_sql_route_never_calls_llm(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    monkeypatch.setattr(answer_module, "complete", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not call LLM")))
    _seed_user_with_transactions(db_session, clerk_id)

    response = client.post(
        "/ask", json={"question": "How much did I spend on food delivery in March?"},
        headers={"Authorization": "Bearer fake-for-test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "sql"
    assert body["used_llm"] is False
    assert "300.00" in body["text"]


def test_ask_vector_route_returns_sources(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    fake_response = LLMResponse(text="answer text citing [budgeting-50-30-20]", provider="groq",
                                 model="llama-3.1-8b-instant", input_tokens=10, output_tokens=5, latency_ms=100.0)
    monkeypatch.setattr(answer_module, "complete", lambda *a, **k: fake_response)
    _seed_user_with_transactions(db_session, clerk_id)

    response = client.post(
        "/ask", json={"question": "What is the 50/30/20 budgeting rule?"},
        headers={"Authorization": "Bearer fake-for-test"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "vector"
    assert body["used_llm"] is True
    assert "budgeting-50-30-20" in body["sources"]
