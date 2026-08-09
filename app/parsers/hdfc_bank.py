"""Deterministic parser for HDFC Bank 'Statement of account' PDFs.

Column positions below are reverse-engineered from the statement layout
(fixed-width table, one row per transaction) rather than guessed from flat
text, because a blank cell (withdrawal OR deposit, never both) makes the
column of a given number ambiguous without knowing where on the page it sits.

Narration is the only column that ever wraps: the renderer performs a plain
greedy character-budget wrap with no word-boundary awareness, so an overflow
line is reattached to the row above it by direct concatenation (no
separator) — the same split can happen mid-word.
"""

import re
from pathlib import Path
from typing import BinaryIO

import pdfplumber

from app.parsers.money import rupees_to_paise
from app.parsers.reconcile import reconcile_bank_statement

# (column, x0_inclusive, x0_exclusive)
COLUMNS = [
    ("date", 30, 88),
    ("narration", 88, 380),
    ("reference", 380, 492),
    ("value_date", 492, 544),
    ("withdrawal", 544, 636),
    ("deposit", 636, 728),
    ("balance", 728, 812),
]

DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{2}$")
TABLE_HEADER_PREFIX = "Date Narration"
FOOTER_MARKER = "SYNTHETIC TEST DATA"

ACCOUNT_NO_RE = re.compile(r"Account No\s*:\s*(\S+)")
IFSC_RE = re.compile(r"RTGS/NEFT IFSC\s*:\s*(\S+)")
PERIOD_RE = re.compile(r"From\s*:\s*(\d{2}/\d{2}/\d{4})\s*To\s*:\s*(\d{2}/\d{2}/\d{4})")


def _column_for(x0: float) -> str | None:
    for name, lo, hi in COLUMNS:
        if lo <= x0 < hi:
            return name
    return None


def _ddmmyy_to_iso(text: str) -> str:
    dd, mm, yy = text.split("/")
    return f"20{yy}-{mm}-{dd}"


def _ddmmyyyy_to_iso(text: str) -> str:
    dd, mm, yyyy = text.split("/")
    return f"{yyyy}-{mm}-{dd}"


def _group_rows(words: list[dict]) -> list[list[dict]]:
    rows: dict[float, list[dict]] = {}
    for w in words:
        key = round(w["top"], 1)
        rows.setdefault(key, []).append(w)
    return [sorted(rows[top], key=lambda w: w["x0"]) for top in sorted(rows)]


def _parse_transaction_row(row: list[dict]) -> dict:
    date_text = None
    narration_words: list[str] = []
    reference_words: list[str] = []
    withdrawal_text = None
    deposit_text = None
    balance_text = None

    for w in row:
        col = _column_for(w["x0"])
        if col == "date" and date_text is None:
            date_text = w["text"]
        elif col == "narration":
            narration_words.append(w["text"])
        elif col == "reference":
            reference_words.append(w["text"])
        elif col == "withdrawal":
            withdrawal_text = w["text"]
        elif col == "deposit":
            deposit_text = w["text"]
        elif col == "balance":
            balance_text = w["text"]

    return {
        "date": _ddmmyy_to_iso(date_text),
        "narration": " ".join(narration_words),
        "reference": "".join(reference_words),
        "withdrawal_paise": rupees_to_paise(withdrawal_text) if withdrawal_text else 0,
        "deposit_paise": rupees_to_paise(deposit_text) if deposit_text else 0,
        "balance_paise": rupees_to_paise(balance_text),
    }


def _merge_continuation(prev_txn: dict, row: list[dict]) -> None:
    overflow = "".join(w["text"] for w in row if _column_for(w["x0"]) == "narration")
    prev_txn["narration"] += overflow


def _extract_header_fields(first_page_text: str) -> dict:
    account_match = ACCOUNT_NO_RE.search(first_page_text)
    ifsc_match = IFSC_RE.search(first_page_text)
    period_match = PERIOD_RE.search(first_page_text)

    account_number = account_match.group(1) if account_match else ""
    masked = "X" * max(0, len(account_number) - 4) + account_number[-4:]

    return {
        "bank": "HDFC BANK",
        "account_number_masked": masked,
        "ifsc": ifsc_match.group(1) if ifsc_match else None,
        "period": {
            "from": _ddmmyyyy_to_iso(period_match.group(1)),
            "to": _ddmmyyyy_to_iso(period_match.group(2)),
        } if period_match else None,
    }


def parse_bank_statement(pdf_path: str | Path | BinaryIO) -> dict:
    with pdfplumber.open(pdf_path) as pdf:
        header = _extract_header_fields(pdf.pages[0].extract_text())

        transactions: list[dict] = []
        for page in pdf.pages:
            rows = _group_rows(page.extract_words())
            in_table = False
            for row in rows:
                row_text = " ".join(w["text"] for w in row)

                if not in_table:
                    if row_text.startswith(TABLE_HEADER_PREFIX):
                        in_table = True
                    continue

                if FOOTER_MARKER in row_text:
                    continue

                first_word = row[0]
                if DATE_RE.match(first_word["text"]) and _column_for(first_word["x0"]) == "date":
                    transactions.append(_parse_transaction_row(row))
                elif transactions:
                    _merge_continuation(transactions[-1], row)

    opening_balance_paise = (
        transactions[0]["balance_paise"] - transactions[0]["deposit_paise"] + transactions[0]["withdrawal_paise"]
        if transactions
        else 0
    )
    closing_balance_paise = transactions[-1]["balance_paise"] if transactions else opening_balance_paise

    statement = {
        **header,
        "opening_balance_paise": opening_balance_paise,
        "closing_balance_paise": closing_balance_paise,
        "total_credits_paise": sum(t["deposit_paise"] for t in transactions),
        "total_debits_paise": sum(t["withdrawal_paise"] for t in transactions),
        "transaction_count": len(transactions),
        "transactions": transactions,
    }

    reconcile_bank_statement(statement)
    return statement
