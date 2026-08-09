"""Sanity checks on the fixture ground truth itself, not on any parser.

If these fail, the fixture is broken and no parser should be written against it.
"""

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
PERSONAS = ["arjun_salaried", "meera_freelance", "rohit_debt", "sneha_young", "vikram_creep"]

NON_PURCHASE_CATEGORIES = {"finance_charge", "tax"}


def load(persona, kind):
    path = FIXTURES / persona / f"{persona}_FY2025-26_{kind}.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("persona", PERSONAS)
def test_bank_reconciles(persona):
    bank = load(persona, "bank")
    opening = bank["opening_balance_paise"]
    credits = bank["total_credits_paise"]
    debits = bank["total_debits_paise"]
    closing = bank["closing_balance_paise"]
    assert opening + credits - debits == closing

    assert sum(t["deposit_paise"] for t in bank["transactions"]) == credits
    assert sum(t["withdrawal_paise"] for t in bank["transactions"]) == debits
    assert len(bank["transactions"]) == bank["transaction_count"]


@pytest.mark.parametrize("persona", PERSONAS)
def test_bank_running_balance(persona):
    bank = load(persona, "bank")
    running = bank["opening_balance_paise"]
    for t in bank["transactions"]:
        running += t["deposit_paise"] - t["withdrawal_paise"]
        assert running == t["balance_paise"], f"{persona} {t['date']}"


@pytest.mark.parametrize("persona", PERSONAS)
def test_card_cycles_chain_and_reconcile(persona):
    card = load(persona, "card")
    prev_closing = 0
    for c in card["cycles"]:
        assert c["opening_paise"] == prev_closing, c["statement_date"]
        assert (
            c["opening_paise"] + c["purchases_paise"] + c["finance_charge_paise"] + c["gst_paise"] - c["payments_paise"]
            == c["closing_paise"]
        ), c["statement_date"]

        debit_purchase_sum = sum(
            t["amount_paise"]
            for t in c["transactions"]
            if t["type"] == "debit" and t.get("expected_category") not in NON_PURCHASE_CATEGORIES
        )
        assert debit_purchase_sum == c["purchases_paise"], c["statement_date"]

        prev_closing = c["closing_paise"]

    assert prev_closing == card["closing_balance_paise"]
    assert sum(c["finance_charge_paise"] for c in card["cycles"]) == card["total_finance_charges_paise"]
