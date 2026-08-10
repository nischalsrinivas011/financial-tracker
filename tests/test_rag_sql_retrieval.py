import uuid
from datetime import date

from app.db.models import Account, Statement, Transaction, User
from app.rag.sql_retrieval import (
    largest_transaction,
    merchant_frequency,
    monthly_totals,
    sum_transactions,
    transaction_count,
)


def _seed(db_session):
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
        opening_balance_paise=0, closing_balance_paise=0,
    )
    db_session.add(statement)
    db_session.flush()

    rows = [
        # date, narration, merchant, category, direction, amount_paise
        (date(2025, 4, 1), "n1", "ZOMATO", "food_delivery", "debit", 30000),
        (date(2025, 4, 15), "n2", "SWIGGY", "food_delivery", "debit", 45000),
        (date(2025, 4, 20), "n3", "ZOMATO", "food_delivery", "debit", 25000),
        (date(2025, 5, 1), "n4", "ZOMATO", "food_delivery", "debit", 60000),
        (date(2025, 4, 1), "n5", "EMPLOYER", "income", "credit", 15000000),
        (date(2025, 4, 3), "n6", "LANDLORD", "rent", "debit", 3800000),
        (date(2025, 4, 10), "n7", "HOME LOAN", "loan_emi", "debit", 2500000),
        (date(2025, 10, 1), "n8", "EMPLOYER", "income", "credit", 15000000),
        (date(2025, 10, 10), "n9", "NETFLIX", "subscription", "debit", 50000),
    ]
    for d, narration, merchant, category, direction, amount in rows:
        db_session.add(Transaction(
            account_id=account.id, statement_id=statement.id, date=d, narration=narration,
            merchant=merchant, category=category, direction=direction, amount_paise=amount,
        ))
    db_session.flush()
    return user, account


def test_sum_transactions_filters_by_category_direction_and_date_range(db_session):
    user, _ = _seed(db_session)

    total = sum_transactions(
        db_session, user.id, category="food_delivery", direction="debit",
        date_from=date(2025, 4, 1), date_to=date(2025, 4, 30),
    )
    assert total == 30000 + 45000 + 25000  # April only, not the May Zomato txn

    income = sum_transactions(db_session, user.id, category="income", direction="credit")
    assert income == 15000000 * 2


def test_transaction_count_matches_sum_filters(db_session):
    user, _ = _seed(db_session)
    count = transaction_count(db_session, user.id, category="food_delivery", direction="debit")
    assert count == 4


def test_largest_transaction_finds_the_max(db_session):
    user, _ = _seed(db_session)
    largest = largest_transaction(db_session, user.id, direction="debit")
    assert largest.merchant == "LANDLORD"
    assert largest.amount_paise == 3800000


def test_monthly_totals_groups_by_month(db_session):
    user, _ = _seed(db_session)
    totals = monthly_totals(db_session, user.id, category="food_delivery", direction="debit")

    by_month = {t["month"]: t["total_paise"] for t in totals}
    assert by_month["2025-04"] == 30000 + 45000 + 25000
    assert by_month["2025-05"] == 60000


def test_merchant_frequency_ranks_by_count(db_session):
    user, _ = _seed(db_session)
    top = merchant_frequency(db_session, user.id, limit=3)

    assert top[0]["merchant"] == "ZOMATO"
    assert top[0]["count"] == 3


def test_results_are_scoped_to_the_requesting_user_only(db_session):
    user_a, _ = _seed(db_session)
    user_b, _ = _seed(db_session)

    assert sum_transactions(db_session, user_a.id, category="income", direction="credit") == 15000000 * 2
    assert sum_transactions(db_session, user_b.id, category="income", direction="credit") == 15000000 * 2
    # Not doubled by the other user's identical seed data - proves the join is scoped correctly.
