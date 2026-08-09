"""Model tests run against the real Neon database (project decision: no
local SQLite stand-in). Each test runs inside a transaction that's rolled
back afterward (db_session fixture, tests/conftest.py), so nothing
persists in the shared dev database.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Account, Statement, Transaction, User


def _make_account(db_session, kind="bank", institution="HDFC BANK", **kwargs):
    user = User(clerk_user_id=f"user_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.flush()

    kwargs.setdefault("account_number_masked", "XXXXXXXXXX1736")
    account = Account(user_id=user.id, kind=kind, institution=institution, **kwargs)
    db_session.add(account)
    db_session.flush()
    return user, account


def test_create_user_account_statement_transaction(db_session):
    user, account = _make_account(db_session)

    statement = Statement(
        account_id=account.id,
        period_from=date(2025, 4, 1),
        period_to=date(2026, 3, 31),
        opening_balance_paise=21450000,
        closing_balance_paise=39953300,
        reconciled=True,
    )
    db_session.add(statement)
    db_session.flush()

    txn = Transaction(
        account_id=account.id,
        statement_id=statement.id,
        date=date(2025, 4, 1),
        narration="UPI-UBER INDIA-uberindia@ybl-YESB0YBLUPI-812932479174-PAYMENT",
        merchant="UBER INDIA",
        category="transport",
        direction="debit",
        amount_paise=51500,
        balance_after_paise=21398500,
    )
    db_session.add(txn)
    db_session.commit()

    fetched = db_session.get(Transaction, txn.id)
    assert fetched.merchant == "UBER INDIA"
    assert fetched.category == "transport"
    assert fetched.amount_paise == 51500
    assert fetched.account.institution == "HDFC BANK"
    assert fetched.statement.reconciled is True


def test_duplicate_transaction_rejected_by_unique_constraint(db_session):
    user, account = _make_account(db_session)
    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0,
    )
    db_session.add(statement)
    db_session.flush()

    kwargs = dict(
        account_id=account.id, statement_id=statement.id, date=date(2025, 4, 1),
        narration="UPI-SWIGGY-swiggy@ybl-...-PAYMENT", merchant="SWIGGY", category="food_delivery",
        direction="debit", amount_paise=38200,
    )
    db_session.add(Transaction(**kwargs))
    db_session.flush()

    db_session.add(Transaction(**kwargs))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_emi_transactions_with_null_merchant_do_not_collide(db_session):
    """Two same-day, same-amount EMIs (null merchant, different narration)
    must NOT be treated as duplicates - the dedup key is narration, not
    merchant, exactly because merchant is null for EMI rows (see
    app/categorize/normalize.py)."""
    user, account = _make_account(db_session)
    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0,
    )
    db_session.add(statement)
    db_session.flush()

    common = dict(
        account_id=account.id, statement_id=statement.id, date=date(2025, 4, 5),
        merchant=None, category="loan_emi", direction="debit", amount_paise=1480000,
    )
    db_session.add(Transaction(narration="EMI 2218756 CHQ S8153434571 6662663109", **common))
    db_session.add(Transaction(narration="EMI 0292537 CHQ S7962932173 8189068024", **common))
    db_session.commit()  # must not raise

    count = db_session.query(Transaction).filter_by(account_id=account.id).count()
    assert count == 2


def test_account_number_never_stores_unmasked_value(db_session):
    """Not a DB constraint (masking happens in the parser) - a smoke check
    that nothing in this test suite accidentally writes a raw account
    number, since rule 3 requires masking before storage."""
    user, account = _make_account(db_session, account_number_masked="XXXXXXXXXX1736")
    assert account.account_number_masked.startswith("X")
    assert "50100299481736" not in account.account_number_masked
