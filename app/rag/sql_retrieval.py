"""SQL retrieval over a user's real transactions - the other half of the
hybrid architecture alongside vector search. Composable aggregation
primitives rather than one hardcoded function per golden question: sum,
largest transaction, monthly totals, and merchant frequency cover all 6
sql-* golden questions and give the hybrid questions a SQL-side building
block to combine with the knowledge corpus.

Every function takes the same optional filters (category, direction,
date_from, date_to) so callers - eventually the router/answer-assembly
layer - compose them rather than each needing a bespoke query.
"""

import uuid
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Account, Transaction


def _filtered(db: Session, user_id: uuid.UUID, *, category=None, direction=None, date_from=None, date_to=None):
    query = (
        db.query(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .filter(Account.user_id == user_id)
    )
    if category is not None:
        query = query.filter(Transaction.category == category)
    if direction is not None:
        query = query.filter(Transaction.direction == direction)
    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)
    return query


def sum_transactions(
    db: Session, user_id: uuid.UUID, *,
    category: str | None = None, direction: str | None = None,
    date_from: date | None = None, date_to: date | None = None,
) -> int:
    total = _filtered(
        db, user_id, category=category, direction=direction, date_from=date_from, date_to=date_to,
    ).with_entities(func.coalesce(func.sum(Transaction.amount_paise), 0)).scalar()
    return int(total)


def transaction_count(
    db: Session, user_id: uuid.UUID, *,
    category: str | None = None, direction: str | None = None,
    date_from: date | None = None, date_to: date | None = None,
) -> int:
    return _filtered(
        db, user_id, category=category, direction=direction, date_from=date_from, date_to=date_to,
    ).count()


def largest_transaction(
    db: Session, user_id: uuid.UUID, *,
    direction: str | None = None, date_from: date | None = None, date_to: date | None = None,
) -> Transaction | None:
    return (
        _filtered(db, user_id, direction=direction, date_from=date_from, date_to=date_to)
        .order_by(Transaction.amount_paise.desc())
        .first()
    )


def monthly_totals(
    db: Session, user_id: uuid.UUID, *,
    category: str | None = None, direction: str | None = None,
    date_from: date | None = None, date_to: date | None = None,
) -> list[dict]:
    month = func.to_char(Transaction.date, "YYYY-MM").label("month")
    rows = (
        _filtered(db, user_id, category=category, direction=direction, date_from=date_from, date_to=date_to)
        .with_entities(month, func.sum(Transaction.amount_paise).label("total_paise"))
        .group_by(month)
        .order_by(month)
        .all()
    )
    return [{"month": m, "total_paise": int(t)} for m, t in rows]


def merchant_frequency(
    db: Session, user_id: uuid.UUID, *,
    date_from: date | None = None, date_to: date | None = None, limit: int = 10,
) -> list[dict]:
    rows = (
        _filtered(db, user_id, date_from=date_from, date_to=date_to)
        .filter(Transaction.merchant.isnot(None))
        .with_entities(Transaction.merchant, func.count().label("count"))
        .group_by(Transaction.merchant)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return [{"merchant": m, "count": c} for m, c in rows]
