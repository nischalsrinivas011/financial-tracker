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


def reconcile_card_statement(statement: dict) -> None:
    prev_closing = 0
    for i, cycle in enumerate(statement["cycles"]):
        if cycle["opening_paise"] != prev_closing:
            raise ReconciliationError(
                f"cycle {i} ({cycle['statement_date']}): opening={cycle['opening_paise']} "
                f"!= prior cycle's closing={prev_closing}"
            )

        expected_closing = (
            cycle["opening_paise"]
            + cycle["purchases_paise"]
            + cycle["finance_charge_paise"]
            + cycle["gst_paise"]
            - cycle["payments_paise"]
        )
        if expected_closing != cycle["closing_paise"]:
            raise ReconciliationError(
                f"cycle {i} ({cycle['statement_date']}): opening+purchases+finance_charge+gst-payments"
                f"={expected_closing} != closing={cycle['closing_paise']}"
            )

        prev_closing = cycle["closing_paise"]

    if prev_closing != statement["closing_balance_paise"]:
        raise ReconciliationError(
            f"final cycle closing={prev_closing} != statement closing_balance_paise="
            f"{statement['closing_balance_paise']}"
        )
