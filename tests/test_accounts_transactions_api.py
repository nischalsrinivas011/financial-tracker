import uuid
from datetime import date

import app.api.deps as deps
from app.db.models import Account, Statement, Transaction, User
from tests.helpers import signed_in


def _seed(db_session, clerk_user_id):
    user = User(clerk_user_id=clerk_user_id)
    db_session.add(user)
    db_session.flush()

    account = Account(
        user_id=user.id, kind="bank", institution="HDFC BANK",
        account_number_masked="XXXXXXXXXX1736", ifsc="HDFC0000512",
    )
    db_session.add(account)
    db_session.flush()

    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0, reconciled=True,
    )
    db_session.add(statement)
    db_session.flush()

    rows = [
        (date(2026, 3, 5), "ZOMATO", "food_delivery", "debit", 30000),
        (date(2026, 3, 10), "SWIGGY", "food_delivery", "debit", 45000),
        (date(2026, 3, 12), "NETFLIX", "subscription", "debit", 50000),
        (date(2025, 4, 1), "EMPLOYER", "income", "credit", 15000000),
    ]
    for d, merchant, category, direction, amount in rows:
        db_session.add(Transaction(
            account_id=account.id, statement_id=statement.id, date=d, narration=merchant,
            merchant=merchant, category=category, direction=direction, amount_paise=amount,
        ))
    db_session.flush()
    return user, account


def _authed(client, monkeypatch, clerk_id: str):
    monkeypatch.setattr(deps, "authenticate_request", lambda request, options: signed_in(clerk_id))


def test_list_accounts_scoped_to_user(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    _seed(db_session, clerk_id)

    response = client.get("/accounts", headers={"Authorization": "Bearer fake"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["institution"] == "HDFC BANK"
    assert body[0]["account_number_masked"] == "XXXXXXXXXX1736"


def test_list_transactions_sorted_newest_first(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    _seed(db_session, clerk_id)

    response = client.get("/transactions", headers={"Authorization": "Bearer fake"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4
    dates = [t["date"] for t in body]
    assert dates == sorted(dates, reverse=True)


def test_list_transactions_filters_by_category(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    _seed(db_session, clerk_id)

    response = client.get(
        "/transactions", params={"category": "food_delivery"}, headers={"Authorization": "Bearer fake"},
    )
    body = response.json()
    assert len(body) == 2
    assert all(t["category"] == "food_delivery" for t in body)


def test_category_summary_excludes_credits_and_sums_correctly(client, monkeypatch, db_session):
    clerk_id = f"user_{uuid.uuid4().hex[:8]}"
    _authed(client, monkeypatch, clerk_id)
    _seed(db_session, clerk_id)

    response = client.get("/transactions/summary", headers={"Authorization": "Bearer fake"})
    body = response.json()
    by_category = {row["category"]: row for row in body}

    assert "income" not in by_category  # credit, excluded
    assert by_category["food_delivery"]["total_paise"] == 30000 + 45000
    assert by_category["food_delivery"]["count"] == 2
    assert by_category["subscription"]["total_paise"] == 50000


def test_endpoints_require_auth(client):
    assert client.get("/accounts").status_code == 401
    assert client.get("/transactions").status_code == 401
    assert client.get("/transactions/summary").status_code == 401
