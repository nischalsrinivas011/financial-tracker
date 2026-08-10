"""Read endpoints for a user's transactions."""

from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession
from app.db.models import Account, Transaction

router = APIRouter(tags=["transactions"])


class TransactionOut(BaseModel):
    id: str
    date: date
    narration: str
    merchant: str | None
    category: str | None
    direction: str
    amount_paise: int


class CategorySummary(BaseModel):
    category: str | None
    total_paise: int
    count: int


def _scoped(db: DbSession, user_id):
    return db.query(Transaction).join(Account, Transaction.account_id == Account.id).filter(Account.user_id == user_id)


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    user: CurrentUser,
    db: DbSession,
    account_id: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=200, le=1000),
):
    query = _scoped(db, user.id)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category:
        query = query.filter(Transaction.category == category)

    transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
    return [
        TransactionOut(
            id=str(t.id), date=t.date, narration=t.narration, merchant=t.merchant,
            category=t.category, direction=t.direction, amount_paise=t.amount_paise,
        )
        for t in transactions
    ]


@router.get("/transactions/summary", response_model=list[CategorySummary])
def category_summary(user: CurrentUser, db: DbSession):
    rows = (
        _scoped(db, user.id)
        .filter(Transaction.direction == "debit")
        .with_entities(Transaction.category, func.sum(Transaction.amount_paise), func.count())
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount_paise).desc())
        .all()
    )
    return [CategorySummary(category=c, total_paise=int(total), count=count) for c, total, count in rows]
