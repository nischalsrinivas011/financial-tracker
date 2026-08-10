"""Best-effort natural-language -> SQL-answer path for the sql route.

Extracting (category, date range, aggregation type) from an arbitrary
question is a real NL-understanding problem; this is rule-based keyword
matching scoped to the golden question set's patterns - same honest
limitation as app/rag/router.py, not a general parser.

No LLM call anywhere in this module: CLAUDE.md requires SQL-only
questions to never trigger a generative call, so this renders plain
templated strings from computed numbers.
"""

import calendar
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.categorize.taxonomy import BANK_CATEGORIES, CARD_CATEGORIES
from app.db.models import Account, Statement
from app.rag.sql_retrieval import (
    largest_transaction,
    merchant_frequency,
    monthly_totals,
    sum_transactions,
    transaction_count,
)

# The demo personas' data covers FY2025-26 (Apr 2025 - Mar 2026); month
# names below are resolved against this fiscal year, not calendar year.
FY_START = date(2025, 4, 1)
FY_END = date(2026, 3, 31)
H1 = (date(2025, 4, 1), date(2025, 9, 30))
H2 = (date(2025, 10, 1), date(2026, 3, 31))

_MONTH_NUMBERS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
_ALL_CATEGORIES = sorted(set(BANK_CATEGORIES) | set(CARD_CATEGORIES))


def _rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def _detect_category(question: str) -> str | None:
    q = question.lower()
    for category in _ALL_CATEGORIES:
        if category.replace("_", " ") in q:
            return category
    return None


def _detect_date_range(question: str) -> tuple[date, date, str]:
    q = question.lower()
    for name, month_num in _MONTH_NUMBERS.items():
        if name in q:
            year = 2026 if month_num <= 3 else 2025
            last_day = calendar.monthrange(year, month_num)[1]
            return date(year, month_num, 1), date(year, month_num, last_day), name.capitalize()
    if "h1" in q or "first half" in q:
        return H1[0], H1[1], "H1 (Apr-Sep 2025)"
    if "h2" in q or "second half" in q:
        return H2[0], H2[1], "H2 (Oct 2025-Mar 2026)"
    if "last quarter" in q:
        return date(2026, 1, 1), date(2026, 3, 31), "the last quarter (Jan-Mar 2026)"
    return FY_START, FY_END, "the fiscal year"


def _has_unreconciled_statement(db: Session, user_id: uuid.UUID, date_from: date, date_to: date) -> bool:
    return (
        db.query(Statement)
        .join(Account, Statement.account_id == Account.id)
        .filter(Account.user_id == user_id)
        .filter(Statement.reconciled.is_(False))
        .filter(Statement.period_from <= date_to, Statement.period_to >= date_from)
        .first()
        is not None
    )


def answer_sql_question(db: Session, user_id: uuid.UUID, question: str) -> str:
    q = question.lower()
    date_from, date_to, period_label = _detect_date_range(question)

    if _has_unreconciled_statement(db, user_id, date_from, date_to):
        return (
            f"A statement covering {period_label} failed reconciliation, so I can't give "
            "you a reliable figure for this period. Please re-check that statement."
        )

    if "largest" in q or "biggest" in q:
        txn = largest_transaction(db, user_id, direction="debit", date_from=date_from, date_to=date_to)
        if txn is None:
            return f"No transactions found for {period_label} - I may not have a statement covering it."
        merchant = txn.merchant or txn.narration
        return f"Your largest transaction in {period_label} was {_rupees(txn.amount_paise)} to {merchant} on {txn.date.isoformat()}."

    if "merchant" in q and ("often" in q or "pay" in q):
        top = merchant_frequency(db, user_id, date_from=date_from, date_to=date_to, limit=1)
        if not top:
            return f"No transactions found for {period_label} - I may not have a statement covering it."
        return f"You paid {top[0]['merchant']} most often in {period_label}: {top[0]['count']} times."

    if "percentage" in q and "income" in q:
        income = sum_transactions(db, user_id, category="income", direction="credit", date_from=date_from, date_to=date_to)
        emi = sum_transactions(db, user_id, category="loan_emi", direction="debit", date_from=date_from, date_to=date_to)
        if income == 0:
            return f"No income transactions found for {period_label}, so I can't compute a percentage."
        pct = emi / income * 100
        return f"In {period_label}, {pct:.1f}% of your income ({_rupees(income)}) went to EMIs ({_rupees(emi)})."

    if "h1" in q and "h2" in q:
        category = _detect_category(question)
        h1_total = sum_transactions(db, user_id, category=category, direction="debit", date_from=H1[0], date_to=H1[1])
        h2_total = sum_transactions(db, user_id, category=category, direction="debit", date_from=H2[0], date_to=H2[1])
        h1_avg, h2_avg = h1_total / 6, h2_total / 6
        return (
            f"Average monthly spend was {_rupees(h1_avg)} in H1 (Apr-Sep) versus "
            f"{_rupees(h2_avg)} in H2 (Oct-Mar), a difference of {_rupees(abs(h1_avg - h2_avg))}."
        )

    if "go up" in q or "trend" in q:
        category = _detect_category(question)
        totals = monthly_totals(db, user_id, category=category, direction="debit")
        if len(totals) < 2:
            label = category.replace("_", " ") if category else "that category"
            return f"Not enough monthly data to determine a trend for {label}."
        first, last = totals[0], totals[-1]
        direction_word = "up" if last["total_paise"] > first["total_paise"] else "down"
        label = category.replace("_", " ") if category else "spending"
        return (
            f"Spending on {label} went {direction_word}: {_rupees(first['total_paise'])} in "
            f"{first['month']} to {_rupees(last['total_paise'])} in {last['month']}."
        )

    category = _detect_category(question)
    if category is None:
        return (
            "I couldn't identify a specific category or place from your question, and I "
            "don't have location data to work from - could you name the category or merchant?"
        )
    total = sum_transactions(db, user_id, category=category, direction="debit", date_from=date_from, date_to=date_to)
    count = transaction_count(db, user_id, category=category, direction="debit", date_from=date_from, date_to=date_to)
    label = category.replace("_", " ")
    if count == 0:
        return f"No transactions found for {label} in {period_label} - I may not have a statement covering that period."
    plural = "s" if count != 1 else ""
    return f"You spent {_rupees(total)} on {label} in {period_label}, across {count} transaction{plural}."
