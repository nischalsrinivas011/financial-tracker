"""Model tests run against the real Neon database (project decision: no
local SQLite stand-in). Each test runs inside a transaction that's rolled
back afterward, so nothing persists in the shared dev database.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Account, Base, Statement, Transaction, User
from app.db.session import engine


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    # create_savepoint: a failed flush inside a test (e.g. an intentional
    # IntegrityError) only rolls back to a SAVEPOINT, not the outer
    # transaction, so this fixture's own rollback below always has a live
    # transaction to close cleanly regardless of what happened in the test.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _make_account(db, kind="bank", institution="HDFC BANK", **kwargs):
    user = User(clerk_user_id=f"user_{uuid.uuid4().hex[:8]}")
    db.add(user)
    db.flush()

    kwargs.setdefault("account_number_masked", "XXXXXXXXXX1736")
    account = Account(user_id=user.id, kind=kind, institution=institution, **kwargs)
    db.add(account)
    db.flush()
    return user, account


def test_create_user_account_statement_transaction(db):
    user, account = _make_account(db)

    statement = Statement(
        account_id=account.id,
        period_from=date(2025, 4, 1),
        period_to=date(2026, 3, 31),
        opening_balance_paise=21450000,
        closing_balance_paise=39953300,
        reconciled=True,
    )
    db.add(statement)
    db.flush()

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
    db.add(txn)
    db.commit()

    fetched = db.get(Transaction, txn.id)
    assert fetched.merchant == "UBER INDIA"
    assert fetched.category == "transport"
    assert fetched.amount_paise == 51500
    assert fetched.account.institution == "HDFC BANK"
    assert fetched.statement.reconciled is True


def test_duplicate_transaction_rejected_by_unique_constraint(db):
    user, account = _make_account(db)
    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0,
    )
    db.add(statement)
    db.flush()

    kwargs = dict(
        account_id=account.id, statement_id=statement.id, date=date(2025, 4, 1),
        narration="UPI-SWIGGY-swiggy@ybl-...-PAYMENT", merchant="SWIGGY", category="food_delivery",
        direction="debit", amount_paise=38200,
    )
    db.add(Transaction(**kwargs))
    db.flush()

    db.add(Transaction(**kwargs))
    with pytest.raises(IntegrityError):
        db.flush()


def test_emi_transactions_with_null_merchant_do_not_collide(db):
    """Two same-day, same-amount EMIs (null merchant, different narration)
    must NOT be treated as duplicates - the dedup key is narration, not
    merchant, exactly because merchant is null for EMI rows (see
    app/categorize/normalize.py)."""
    user, account = _make_account(db)
    statement = Statement(
        account_id=account.id, period_from=date(2025, 4, 1), period_to=date(2026, 3, 31),
        opening_balance_paise=0, closing_balance_paise=0,
    )
    db.add(statement)
    db.flush()

    common = dict(
        account_id=account.id, statement_id=statement.id, date=date(2025, 4, 5),
        merchant=None, category="loan_emi", direction="debit", amount_paise=1480000,
    )
    db.add(Transaction(narration="EMI 2218756 CHQ S8153434571 6662663109", **common))
    db.add(Transaction(narration="EMI 0292537 CHQ S7962932173 8189068024", **common))
    db.commit()  # must not raise

    count = db.query(Transaction).filter_by(account_id=account.id).count()
    assert count == 2


def test_account_number_never_stores_unmasked_value(db):
    """Not a DB constraint (masking happens in the parser) - a smoke check
    that nothing in this test suite accidentally writes a raw account
    number, since rule 3 requires masking before storage."""
    user, account = _make_account(db, account_number_masked="XXXXXXXXXX1736")
    assert account.account_number_masked.startswith("X")
    assert "50100299481736" not in account.account_number_masked
