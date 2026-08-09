"""Deterministic parser for credit card statements in this project's fixture template.

Not issuer-specific despite appearances: the 5 synthetic personas carry 5
different issuers (HDFC, ICICI, SBI, Axis, Kotak), but the generator
(scripts/statement_generator/render_card.py) renders all of them from one
shared PDF template. A real HDFC card statement and a real SBI card
statement would not actually share a layout in the wild — if real statements
are ever parsed, this will need to split into per-issuer parsers the same
way hdfc_bank.py is bank-specific. One module is correct only because the
synthetic data has one layout.

Shape is deliberately unlike the bank statement: one page per billing cycle,
a label/value summary block instead of a running balance, and a transaction
ledger where amount and direction (Cr/Dr) are always both printed — so unlike
the bank parser, there's no blank-cell ambiguity and flat-text regex per line
is enough; word x-position bucketing isn't needed here.

Scope note: every fixture has exactly one page per cycle (max ~13
transactions per cycle). A cycle spilling onto a second page would need a new
fixture and a follow-up — not handled here since it can't be tested yet.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import pdfplumber

from app.parsers.money import rupees_to_paise
from app.parsers.reconcile import ReconciliationError, reconcile_card_statement

# Not start-anchored: the cardholder address block and this "key figures"
# panel sit at overlapping y-positions, so extract_text() sometimes prepends
# a stray address line to these before the label appears on the same line.
STATEMENT_DATE_RE = re.compile(r"Statement Date\s+(\d{2} \w{3} \d{4})$")
DUE_DATE_RE = re.compile(r"Payment Due Date\s+(\d{2} \w{3} \d{4})$")
KEY_FIGURE_CLOSING_RE = re.compile(r"Total Amount Due Rs\.\s*([\d,]+\.\d{2})$")
MINIMUM_DUE_RE = re.compile(r"Minimum Amount Due Rs\.\s*([\d,]+\.\d{2})$")

PREVIOUS_BALANCE_RE = re.compile(r"^Previous Balance\s+(-?[\d,]+\.\d{2})$")
PAYMENTS_RE = re.compile(r"^Payments / Credits\s+(-?[\d,]+\.\d{2})$")
PURCHASES_RE = re.compile(r"^Purchases & Other Debits\s+(-?[\d,]+\.\d{2})$")
FINANCE_CHARGE_RE = re.compile(r"^Finance Charges\s+(-?[\d,]+\.\d{2})$")
GST_RE = re.compile(r"^GST\s+(-?[\d,]+\.\d{2})$")
SUMMARY_CLOSING_RE = re.compile(r"^Total Amount Due\s+(-?[\d,]+\.\d{2})$")

# MULTILINE: these two are searched against the whole first page's text
# rather than line-by-line, so ^/$ must anchor to line boundaries, not just
# the start/end of the full string.
CREDIT_LIMIT_RE = re.compile(r"^Credit Limit: Rs\.\s*([\d,]+\.\d{2})", re.MULTILINE)
CARD_NO_RE = re.compile(r"Card No: XXXX XXXX XXXX (\d{4})")
PRODUCT_RE = re.compile(r"^(.*?)\s+Card No: XXXX XXXX XXXX \d{4}$", re.MULTILINE)

TRANSACTIONS_HEADER = "Date Transaction Description"
FOOTER_MARKER = "SYNTHETIC TEST DATA"
TRANSACTION_RE = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?[\d,]+\.\d{2})\s+(Cr|Dr)$")


def _ddmonyyyy_to_iso(text: str) -> str:
    return datetime.strptime(text, "%d %b %Y").date().isoformat()


def _ddmmyyyy_to_iso(text: str) -> str:
    dd, mm, yyyy = text.split("/")
    return f"{yyyy}-{mm}-{dd}"


def _parse_cycle(text: str) -> dict:
    statement_date = due_date = None
    key_figure_closing = minimum_due = None
    opening = payments = purchases = finance_charge = gst = summary_closing = None
    transactions = []
    in_transactions = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if m := STATEMENT_DATE_RE.search(line):
            statement_date = _ddmonyyyy_to_iso(m.group(1))
        elif m := DUE_DATE_RE.search(line):
            due_date = _ddmonyyyy_to_iso(m.group(1))
        elif m := KEY_FIGURE_CLOSING_RE.search(line):
            key_figure_closing = rupees_to_paise(m.group(1))
        elif m := MINIMUM_DUE_RE.search(line):
            minimum_due = rupees_to_paise(m.group(1))
        elif m := PREVIOUS_BALANCE_RE.match(line):
            opening = rupees_to_paise(m.group(1))
        elif m := PAYMENTS_RE.match(line):
            payments = abs(rupees_to_paise(m.group(1)))
        elif m := PURCHASES_RE.match(line):
            purchases = rupees_to_paise(m.group(1))
        elif m := FINANCE_CHARGE_RE.match(line):
            finance_charge = rupees_to_paise(m.group(1))
        elif m := GST_RE.match(line):
            gst = rupees_to_paise(m.group(1))
        elif m := SUMMARY_CLOSING_RE.match(line):
            summary_closing = rupees_to_paise(m.group(1))
        elif line.startswith(TRANSACTIONS_HEADER):
            in_transactions = True
        elif FOOTER_MARKER in line:
            in_transactions = False
        elif in_transactions and (m := TRANSACTION_RE.match(line)):
            transactions.append({
                "date": _ddmmyyyy_to_iso(m.group(1)),
                "description": m.group(2),
                "amount_paise": rupees_to_paise(m.group(3)),
                "type": "credit" if m.group(4) == "Cr" else "debit",
            })

    if key_figure_closing != summary_closing:
        raise ReconciliationError(
            f"cycle {statement_date}: key-figure Total Amount Due={key_figure_closing} "
            f"!= account-summary Total Amount Due={summary_closing}"
        )

    return {
        "statement_date": statement_date,
        "due_date": due_date,
        "opening_paise": opening,
        "payments_paise": payments,
        "purchases_paise": purchases,
        "finance_charge_paise": finance_charge,
        "gst_paise": gst,
        "closing_paise": summary_closing,
        "minimum_due_paise": minimum_due,
        "transactions": transactions,
    }


def parse_card_statement(pdf_path: str | Path | BinaryIO) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        pages_text = [page.extract_text() for page in pdf.pages]

    first_page = pages_text[0]
    issuer = first_page.splitlines()[0].strip()
    product_match = PRODUCT_RE.search(first_page)
    card_no_match = CARD_NO_RE.search(first_page)
    credit_limit_match = CREDIT_LIMIT_RE.search(first_page)

    cycles = [_parse_cycle(text) for text in pages_text]

    statement = {
        "issuer": issuer,
        "product": product_match.group(1).strip() if product_match else None,
        "card_number_masked": "X" * 12 + card_no_match.group(1) if card_no_match else None,
        "credit_limit_paise": rupees_to_paise(credit_limit_match.group(1)) if credit_limit_match else None,
        "cycle_count": len(cycles),
        "total_finance_charges_paise": sum(c["finance_charge_paise"] for c in cycles),
        "total_gst_paise": sum(c["gst_paise"] for c in cycles),
        "closing_balance_paise": cycles[-1]["closing_paise"] if cycles else 0,
        "cycles": cycles,
    }

    reconcile_card_statement(statement)
    return statement
