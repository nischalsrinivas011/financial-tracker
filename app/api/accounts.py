"""Read endpoints for a user's accounts."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, DbSession
from app.db.models import Account

router = APIRouter(tags=["accounts"])


class AccountOut(BaseModel):
    id: str
    kind: str
    institution: str
    product: str | None
    account_number_masked: str


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(user: CurrentUser, db: DbSession):
    accounts = db.query(Account).filter_by(user_id=user.id).order_by(Account.created_at).all()
    return [
        AccountOut(
            id=str(a.id), kind=a.kind, institution=a.institution,
            product=a.product, account_number_masked=a.account_number_masked,
        )
        for a in accounts
    ]
