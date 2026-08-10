import uuid
from datetime import date

from app.db.models import Account, Statement, Transaction, User
from app.rag.sql_answer import answer_sql_question


def _seed(db_session, *, unreconciled_april=False):
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
        opening_balance_paise=0, closing_balance_paise=0, reconciled=not unreconciled_april,
    )
    db_session.add(statement)
    db_session.flush()

    rows = [
        (date(2026, 3, 5), "n1", "ZOMATO", "food_delivery", "debit", 30000),  # March = FY2025-26's March = 2026
        (date(2026, 3, 15), "n2", "SWIGGY", "food_delivery", "debit", 45000),
        (date(2025, 4, 1), "n3", "EMPLOYER", "income", "credit", 15000000),
        (date(2025, 4, 10), "n4", "HOME LOAN", "loan_emi", "debit", 3000000),
        (date(2025, 4, 3), "n5", "LANDLORD", "rent", "debit", 3800000),
        (date(2025, 4, 20), "n6", "ZOMATO", "food_delivery", "debit", 25000),
        (date(2025, 5, 1), "n7", "ZOMATO", "food_delivery", "debit", 60000),
        (date(2025, 10, 1), "n8", "SWIGGY", "food_delivery", "debit", 12000),
        (date(2025, 4, 5), "n9", "AMAZON", "shopping", "debit", 500000),
        (date(2026, 2, 10), "n10", "AMAZON", "shopping", "debit", 700000),  # last quarter (Jan-Mar 2026)
        (date(2026, 2, 15), "n11", "FLIPKART", "shopping", "debit", 200000),
        (date(2025, 6, 1), "n12", "ZOMATO", "food_delivery", "debit", 20000),  # breaks the ZOMATO/AMAZON tie
    ]
    for d, narration, merchant, category, direction, amount in rows:
        db_session.add(Transaction(
            account_id=account.id, statement_id=statement.id, date=d, narration=narration,
            merchant=merchant, category=category, direction=direction, amount_paise=amount,
        ))
    db_session.flush()
    return user, account


def test_category_and_month_sum(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "How much did I spend on food delivery in March?")
    assert "₹750.00" in text  # 30000 + 45000 paise = 75000 paise = ₹750.00
    assert "2" in text  # transaction count


def test_no_data_for_period_says_so_not_zero(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "How much did I spend on food delivery in February?")
    assert "No transactions found" in text
    assert "₹0.00" not in text


def test_largest_transaction(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "What was my largest single transaction last quarter?")
    assert "AMAZON" in text
    assert "₹7,000.00" in text


def test_merchant_frequency(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "Which merchant did I pay most often?")
    assert "ZOMATO" in text


def test_percentage_of_income_to_emi(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "What percentage of my income went to EMIs?")
    assert "20.0%" in text  # 3000000 / 15000000 = 20%


def test_h1_vs_h2_comparison(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "Compare my average monthly spend in H1 versus H2.")
    assert "H1" in text and "H2" in text


def test_unreconciled_statement_is_surfaced_not_analyzed(db_session):
    user, _ = _seed(db_session, unreconciled_april=True)
    text = answer_sql_question(db_session, user.id, "Why did my balance drop in April?")
    assert "reconciliation" in text.lower()


def test_unidentifiable_category_asks_for_clarification(db_session):
    user, _ = _seed(db_session)
    text = answer_sql_question(db_session, user.id, "What did I spend at that place near my office?")
    assert "clarification" in text.lower() or "could you" in text.lower()
