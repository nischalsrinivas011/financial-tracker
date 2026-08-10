import uuid
from datetime import date

import app.rag.answer as answer_module
from app.db.models import Account, Statement, Transaction, User
from app.llm.client import AllProvidersExhaustedError, LLMResponse
from app.rag.answer import answer


def _seed_user_with_transactions(db_session):
    user = User(clerk_user_id=f"user_{uuid.uuid4().hex[:8]}")
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


def _fake_llm_response(text="a synthesized answer citing [budgeting-50-30-20]"):
    return LLMResponse(text=text, provider="groq", model="llama-3.1-8b-instant",
                        input_tokens=50, output_tokens=10, latency_ms=100.0)


def test_refuse_route_never_calls_llm(db_session, monkeypatch):
    called = []
    monkeypatch.setattr(answer_module, "complete", lambda *a, **k: called.append(1))

    user = _seed_user_with_transactions(db_session)
    result = answer(db_session, user.id, "Which mutual fund should I buy?")

    assert result.route == "refuse"
    assert result.used_llm is False
    assert called == []


def test_sql_route_never_calls_llm(db_session, monkeypatch):
    called = []
    monkeypatch.setattr(answer_module, "complete", lambda *a, **k: called.append(1))

    user = _seed_user_with_transactions(db_session)
    result = answer(db_session, user.id, "How much did I spend on food delivery in March?")

    assert result.route == "sql"
    assert result.used_llm is False
    assert "₹300.00" in result.text
    assert called == []


def test_vector_route_calls_llm_and_returns_sources(db_session, monkeypatch):
    monkeypatch.setattr(answer_module, "complete", lambda *a, **k: _fake_llm_response())

    user = _seed_user_with_transactions(db_session)
    result = answer(db_session, user.id, "What is the 50/30/20 budgeting rule?")

    assert result.route == "vector"
    assert result.used_llm is True
    assert "budgeting-50-30-20" in result.sources
    assert result.text == "a synthesized answer citing [budgeting-50-30-20]"


def test_hybrid_route_includes_sql_context_in_the_prompt(db_session, monkeypatch):
    captured = {}

    def fake_complete(messages, **kwargs):
        captured["prompt"] = messages[0]["content"]
        return _fake_llm_response("hybrid synthesized answer")

    monkeypatch.setattr(answer_module, "complete", fake_complete)

    user = _seed_user_with_transactions(db_session)
    result = answer(db_session, user.id, "Should I prepay my home loan or invest the surplus?")

    assert result.route == "hybrid"
    assert result.used_llm is True
    assert "User's actual data:" in captured["prompt"]
    assert "prepay-vs-invest" in result.sources


def test_llm_unavailable_falls_back_to_raw_chunks_instead_of_crashing(db_session, monkeypatch):
    def raise_exhausted(*a, **k):
        raise AllProvidersExhaustedError("no provider configured")

    monkeypatch.setattr(answer_module, "complete", raise_exhausted)

    user = _seed_user_with_transactions(db_session)
    result = answer(db_session, user.id, "What is the 50/30/20 budgeting rule?")

    assert result.route == "vector"
    assert result.used_llm is False
    assert len(result.text) > 0
    assert "budgeting-50-30-20" in result.sources
