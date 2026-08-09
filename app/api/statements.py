"""Statement upload endpoints: PDF in, parsed + categorized + stored.

Reconciliation (money math) is a hard gate - a statement that fails it
never reaches storage (rule: never surface unreconciled data as valid),
via ReconciliationError -> HTTP 422. Categorization is best-effort on
top: an unresolvable merchant still gets stored, just with
category/merchant left null, since losing transaction data over a naming
failure would be worse than an incomplete category.

A card upload contains multiple billing cycles, so it creates multiple
Statement rows (one per cycle, matching what "statement" means on a real
card) linked to one Account; a bank upload creates exactly one.
"""

import io
from datetime import date

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.api.deps import CurrentUser, DbSession
from app.categorize.cascade import (
    UnresolvedCategoryError,
    categorize_bank_transaction,
    categorize_card_transaction,
)
from app.db.models import Account, Statement, Transaction
from app.parsers.card_statement import parse_card_statement
from app.parsers.hdfc_bank import parse_bank_statement
from app.parsers.reconcile import ReconciliationError

router = APIRouter(prefix="/statements", tags=["statements"])


class StatementUploadResult(BaseModel):
    account_id: str
    statement_ids: list[str]
    transactions_parsed: int
    transactions_stored: int
    transactions_uncategorized: int


def _get_or_create_account(
    db: DbSession, user, *, kind: str, institution: str, account_number_masked: str,
    product: str | None = None, ifsc: str | None = None,
) -> Account:
    account = (
        db.query(Account)
        .filter_by(user_id=user.id, kind=kind, account_number_masked=account_number_masked)
        .one_or_none()
    )
    if account is None:
        account = Account(
            user_id=user.id, kind=kind, institution=institution,
            account_number_masked=account_number_masked, product=product, ifsc=ifsc,
        )
        db.add(account)
        db.flush()
    return account


def _insert_transactions(db: DbSession, rows: list[dict]) -> int:
    if not rows:
        return 0
    # RETURNING, not rowcount: a batched multi-row ON CONFLICT DO NOTHING
    # insert doesn't reliably populate rowcount through psycopg/SQLAlchemy
    # (observed -1 in testing). RETURNING only yields rows that were
    # actually inserted - a conflicted row produces no output row - so
    # counting what comes back is exact regardless of that driver quirk.
    stmt = (
        pg_insert(Transaction)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["account_id", "date", "amount_paise", "narration"])
        .returning(Transaction.id)
    )
    result = db.execute(stmt)
    return len(result.fetchall())


@router.post("/bank", response_model=StatementUploadResult)
def upload_bank_statement(user: CurrentUser, db: DbSession, file: UploadFile = File(...)):
    try:
        parsed = parse_bank_statement(io.BytesIO(file.file.read()))
    except ReconciliationError as exc:
        raise HTTPException(status_code=422, detail=f"statement failed reconciliation: {exc}") from exc

    account = _get_or_create_account(
        db, user, kind="bank", institution=parsed["bank"],
        account_number_masked=parsed["account_number_masked"], ifsc=parsed["ifsc"],
    )

    statement = Statement(
        account_id=account.id,
        period_from=date.fromisoformat(parsed["period"]["from"]),
        period_to=date.fromisoformat(parsed["period"]["to"]),
        opening_balance_paise=parsed["opening_balance_paise"],
        closing_balance_paise=parsed["closing_balance_paise"],
        reconciled=True,
    )
    db.add(statement)
    db.flush()

    rows = []
    uncategorized = 0
    for txn in parsed["transactions"]:
        try:
            resolved = categorize_bank_transaction(txn["narration"], parsed["bank"])
            merchant, category = resolved["merchant"], resolved["category"]
        except UnresolvedCategoryError:
            merchant, category = None, None
            uncategorized += 1

        rows.append(dict(
            account_id=account.id, statement_id=statement.id,
            date=date.fromisoformat(txn["date"]), narration=txn["narration"],
            merchant=merchant, category=category,
            direction="credit" if txn["deposit_paise"] else "debit",
            amount_paise=txn["deposit_paise"] or txn["withdrawal_paise"],
            balance_after_paise=txn["balance_paise"],
        ))

    stored = _insert_transactions(db, rows)
    db.commit()

    return StatementUploadResult(
        account_id=str(account.id), statement_ids=[str(statement.id)],
        transactions_parsed=len(rows), transactions_stored=stored,
        transactions_uncategorized=uncategorized,
    )


@router.post("/card", response_model=StatementUploadResult)
def upload_card_statement(user: CurrentUser, db: DbSession, file: UploadFile = File(...)):
    try:
        parsed = parse_card_statement(io.BytesIO(file.file.read()))
    except ReconciliationError as exc:
        raise HTTPException(status_code=422, detail=f"statement failed reconciliation: {exc}") from exc

    account = _get_or_create_account(
        db, user, kind="credit_card", institution=parsed["issuer"],
        account_number_masked=parsed["card_number_masked"], product=parsed["product"],
    )

    statement_ids: list[str] = []
    total_rows = 0
    total_stored = 0
    uncategorized = 0

    for cycle in parsed["cycles"]:
        cycle_statement_date = date.fromisoformat(cycle["statement_date"])
        txn_dates = [date.fromisoformat(t["date"]) for t in cycle["transactions"]]
        period_from = min(txn_dates) if txn_dates else cycle_statement_date

        statement = Statement(
            account_id=account.id,
            period_from=period_from, period_to=cycle_statement_date,
            opening_balance_paise=cycle["opening_paise"],
            closing_balance_paise=cycle["closing_paise"],
            reconciled=True,
        )
        db.add(statement)
        db.flush()
        statement_ids.append(str(statement.id))

        rows = []
        for txn in cycle["transactions"]:
            try:
                resolved = categorize_card_transaction(txn["description"])
                merchant, category = resolved["merchant"], resolved["category"]
            except UnresolvedCategoryError:
                merchant, category = None, None
                uncategorized += 1

            rows.append(dict(
                account_id=account.id, statement_id=statement.id,
                date=date.fromisoformat(txn["date"]), narration=txn["description"],
                merchant=merchant, category=category,
                direction=txn["type"],
                amount_paise=txn["amount_paise"],
                balance_after_paise=None,
            ))

        total_rows += len(rows)
        total_stored += _insert_transactions(db, rows)

    db.commit()

    return StatementUploadResult(
        account_id=str(account.id), statement_ids=statement_ids,
        transactions_parsed=total_rows, transactions_stored=total_stored,
        transactions_uncategorized=uncategorized,
    )
