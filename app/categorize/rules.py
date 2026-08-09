"""Stage 1 of the categorisation cascade: category decided by narration
*shape* alone, independent of which merchant/counterparty it is.

Only shapes that are unambiguous regardless of merchant go here (verified
against all 5 fixture personas — e.g. every NEFT DR row is a rent payment,
every SI-TAD row is a SIP). Shapes where the category genuinely depends on
which merchant it is (UPI, POS, IB BILLPAY, ACH D) are deliberately left to
the merchant lookup table (stage 2) instead of being hardcoded here — e.g.
every POS row in this dataset happens to be dining, but a POS terminal
isn't dining-specific in general, so encoding that as a rule would be a
dataset artifact masquerading as a fact.
"""

CARD_DESCRIPTION_CATEGORIES = {
    "FINANCE CHARGES": "finance_charge",
    "GST ON FINANCE CHARGES": "tax",
    "PAYMENT RECEIVED - THANK YOU": "payment",
    "CASH ADVANCE ATM": "cash_advance",
}


def apply_bank_rules(narration: str, merchant: str | None) -> str | None:
    if narration.startswith("NEFT CR-"):
        return "income"
    if narration.startswith("NEFT DR-"):
        return "rent"
    if narration.startswith("SI-TAD-"):
        return "investment_sip"
    if narration.startswith("EMI "):
        return "loan_emi"
    if narration == "CREDIT INTEREST CAPITALISED":
        return "interest_income"
    if narration.startswith("ATW-"):
        return "cash_withdrawal"
    if narration.startswith("IMPS"):
        # merchant is the purpose field (see normalize.py): fund-redemption
        # and self-transfers are structural, everything else is a transfer
        # to a named person - can't be a lookup table, names are unbounded.
        if merchant and (merchant.startswith("MF ") or merchant.startswith("SELF")):
            return "transfer_in"
        return "family_transfer"
    return None


def apply_card_rules(description: str) -> str | None:
    return CARD_DESCRIPTION_CATEGORIES.get(description)
