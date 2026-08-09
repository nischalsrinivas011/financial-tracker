class ReconciliationError(Exception):
    """Raised when a parsed statement's figures don't add up.

    Per project rule: an unreconciled statement must never be surfaced as if
    it were valid, so parsers raise this instead of returning a result.
    """


def reconcile_bank_statement(statement: dict) -> None:
    opening = statement["opening_balance_paise"]
    closing = statement["closing_balance_paise"]
    credits = statement["total_credits_paise"]
    debits = statement["total_debits_paise"]

    if opening + credits - debits != closing:
        raise ReconciliationError(
            f"opening({opening}) + credits({credits}) - debits({debits}) "
            f"!= closing({closing})"
        )

    running = opening
    for i, txn in enumerate(statement["transactions"]):
        running += txn["deposit_paise"] - txn["withdrawal_paise"]
        if running != txn["balance_paise"]:
            raise ReconciliationError(
                f"running balance mismatch at transaction {i} ({txn['date']}): "
                f"computed={running} stated={txn['balance_paise']}"
            )
