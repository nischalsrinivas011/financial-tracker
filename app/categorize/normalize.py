"""Extract a merchant/counterparty name out of a raw bank narration.

HDFC narrations come in about nine fixed shapes (verified against all 1,792
transactions across the 5 fixture personas); each shape puts the merchant in
a different position, so this dispatches on the narration's prefix rather
than using one universal regex.

Known, permanent gap: EMI narrations ("EMI 2218756 CHQ S8153434571
6662663109") never print the loan type anywhere in the statement text — a
real HDFC EMI auto-debit narration doesn't carry it either. There is no
text signal to extract it from, so this returns None for EMI rows rather
than guessing. The categorisation cascade still assigns the correct
category (loan_emi) from the narration shape alone.

Card statement descriptions need no extraction — SBI-template card
statements print the merchant directly (`SWIGGY`, `FLIPKART`), so
`normalize_card_merchant` is a thin pass-through kept only so callers don't
have to special-case bank vs. card.
"""


def normalize_bank_merchant(narration: str, bank_name: str) -> str | None:
    if narration.startswith("UPI-"):
        return narration.split("-")[1]

    if narration.startswith("POS "):
        body = narration[len("POS "):-len(" POS DEBIT")]
        _, merchant = body.split(" ", 1)
        return merchant

    if narration.startswith("NEFT CR-") or narration.startswith("NEFT DR-"):
        return narration.split("-")[2]

    if narration.startswith("SI-TAD-"):
        return narration.split("-")[2]

    if narration.startswith("IB BILLPAY"):
        return narration.split("-")[1]

    if narration.startswith("ACH D-"):
        return narration.split("-")[1].strip()

    if narration.startswith("ATW-"):
        return narration.split("-")[2]

    if narration.startswith("IMPS"):
        # IMPS-<ref>-<merchant, which may itself contain hyphens>-<bank code>
        parts = narration.split("-")
        return "-".join(parts[2:-1])

    if narration == "CREDIT INTEREST CAPITALISED":
        return bank_name

    if narration.startswith("EMI "):
        return None

    return None


def normalize_card_merchant(description: str) -> str:
    return description
