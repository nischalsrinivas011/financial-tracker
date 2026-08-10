"""Statement upload endpoint tests, using the real Phase 1 fixture PDFs
end-to-end through parse -> categorize -> store. Clerk is mocked (see
tests/helpers.py); DB writes hit real Neon via the rollback-per-test
db_session fixture (tests/conftest.py).
"""

import uuid
from pathlib import Path

import app.api.deps as deps
from app.db.models import Account, Statement, Transaction
from tests.helpers import signed_in, signed_out

FIXTURES = Path(__file__).parent / "fixtures"


def _authed_client(client, monkeypatch):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_in(clerk_id))
    return client


def _upload(client, endpoint, path):
    with open(path, "rb") as f:
        return client.post(
            endpoint,
            files={"file": (path.name, f, "application/pdf")},
            headers={"Authorization": "Bearer fake-for-test"},
        )


def test_upload_bank_statement_end_to_end(client, monkeypatch, db_session):
    _authed_client(client, monkeypatch)
    pdf = FIXTURES / "arjun_salaried" / "arjun_salaried_FY2025-26_bank.pdf"

    response = _upload(client, "/statements/bank", pdf)
    assert response.status_code == 200
    body = response.json()

    assert body["transactions_parsed"] == 370
    assert body["transactions_stored"] == 370
    assert len(body["statement_ids"]) == 1

    account = db_session.get(Account, uuid.UUID(body["account_id"]))
    assert account.kind == "bank"
    assert account.institution == "HDFC BANK"

    statement = db_session.get(Statement, uuid.UUID(body["statement_ids"][0]))
    assert statement.reconciled is True

    stored_count = db_session.query(Transaction).filter_by(account_id=account.id).count()
    assert stored_count == 370

    # Spot-check one known transaction categorized correctly end-to-end.
    salary = (
        db_session.query(Transaction)
        .filter_by(account_id=account.id, category="income")
        .first()
    )
    assert salary is not None
    assert salary.merchant == "ZENTRIX LABS PVT LTD"


def test_reuploading_same_bank_statement_dedupes_transactions(client, monkeypatch, db_session):
    _authed_client(client, monkeypatch)
    pdf = FIXTURES / "meera_freelance" / "meera_freelance_FY2025-26_bank.pdf"

    first = _upload(client, "/statements/bank", pdf).json()
    second = _upload(client, "/statements/bank", pdf).json()

    assert first["account_id"] == second["account_id"]
    assert second["transactions_stored"] == 0
    assert second["transactions_parsed"] == first["transactions_parsed"]

    account_id = uuid.UUID(first["account_id"])
    total = db_session.query(Transaction).filter_by(account_id=account_id).count()
    assert total == first["transactions_parsed"]


def test_upload_card_statement_creates_one_statement_per_cycle(client, monkeypatch, db_session):
    _authed_client(client, monkeypatch)
    pdf = FIXTURES / "rohit_debt" / "rohit_debt_FY2025-26_card.pdf"

    response = _upload(client, "/statements/card", pdf)
    assert response.status_code == 200
    body = response.json()

    assert len(body["statement_ids"]) == 12

    account = db_session.get(Account, uuid.UUID(body["account_id"]))
    assert account.kind == "credit_card"
    assert account.institution == "SBI CARD"

    statements = db_session.query(Statement).filter_by(account_id=account.id).all()
    assert len(statements) == 12
    assert all(s.reconciled for s in statements)


def test_upload_requires_auth(client, monkeypatch, db_session):
    # Counts compared before/after, not asserted as 0: the shared Neon
    # database also holds real, persistent eval-persona seed data
    # (eval/seed_persona.py) outside this test's transaction.
    accounts_before = db_session.query(Account).count()
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_out())
    pdf = FIXTURES / "arjun_salaried" / "arjun_salaried_FY2025-26_bank.pdf"

    response = _upload(client, "/statements/bank", pdf)
    assert response.status_code == 401
    assert db_session.query(Account).count() == accounts_before


def test_reconciliation_failure_returns_422_and_stores_nothing(client, monkeypatch, db_session):
    import app.api.statements as statements_module
    from app.parsers.reconcile import ReconciliationError

    accounts_before = db_session.query(Account).count()
    statements_before = db_session.query(Statement).count()

    _authed_client(client, monkeypatch)
    monkeypatch.setattr(
        statements_module, "parse_bank_statement",
        lambda f: (_ for _ in ()).throw(ReconciliationError("simulated mismatch")),
    )
    pdf = FIXTURES / "arjun_salaried" / "arjun_salaried_FY2025-26_bank.pdf"

    response = _upload(client, "/statements/bank", pdf)
    assert response.status_code == 422
    assert db_session.query(Account).count() == accounts_before
    assert db_session.query(Statement).count() == statements_before
