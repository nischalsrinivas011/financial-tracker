import json
from pathlib import Path

import pytest

from app.parsers.card_statement import parse_card_statement
from app.parsers.reconcile import ReconciliationError, reconcile_card_statement

FIXTURES = Path(__file__).parent / "fixtures"
PERSONAS = ["arjun_salaried", "meera_freelance", "rohit_debt", "sneha_young", "vikram_creep"]

CYCLE_FIELDS = [
    "statement_date", "due_date", "opening_paise", "payments_paise", "purchases_paise",
    "finance_charge_paise", "gst_paise", "closing_paise", "minimum_due_paise",
]
TXN_FIELDS = ["date", "description", "amount_paise", "type"]


def load_expected(persona):
    path = FIXTURES / persona / f"{persona}_FY2025-26_card.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("persona", PERSONAS)
def test_header_fields(persona):
    expected = load_expected(persona)
    result = parse_card_statement(FIXTURES / persona / f"{persona}_FY2025-26_card.pdf")

    assert result["issuer"] == expected["issuer"]
    assert result["product"] == expected["product"]
    assert result["card_number_masked"] == expected["card_number_masked"]
    assert result["credit_limit_paise"] == expected["credit_limit_paise"]
    assert result["cycle_count"] == expected["cycle_count"] == len(result["cycles"])


@pytest.mark.parametrize("persona", PERSONAS)
def test_totals(persona):
    expected = load_expected(persona)
    result = parse_card_statement(FIXTURES / persona / f"{persona}_FY2025-26_card.pdf")

    assert result["total_finance_charges_paise"] == expected["total_finance_charges_paise"]
    assert result["total_gst_paise"] == expected["total_gst_paise"]
    assert result["closing_balance_paise"] == expected["closing_balance_paise"]


@pytest.mark.parametrize("persona", PERSONAS)
def test_cycles_match_fixture_exactly(persona):
    expected = load_expected(persona)
    result = parse_card_statement(FIXTURES / persona / f"{persona}_FY2025-26_card.pdf")

    for i, (got, want) in enumerate(zip(result["cycles"], expected["cycles"])):
        for field in CYCLE_FIELDS:
            assert got[field] == want[field], f"{persona} cycle {i} field {field}"

        assert len(got["transactions"]) == len(want["transactions"]), f"{persona} cycle {i} txn count"
        for j, (got_t, want_t) in enumerate(zip(got["transactions"], want["transactions"])):
            for field in TXN_FIELDS:
                assert got_t[field] == want_t[field], f"{persona} cycle {i} txn {j} field {field}"


@pytest.mark.parametrize("persona", PERSONAS)
def test_parsed_statement_reconciles(persona):
    result = parse_card_statement(FIXTURES / persona / f"{persona}_FY2025-26_card.pdf")
    reconcile_card_statement(result)


def test_reconciliation_gate_rejects_a_broken_statement():
    broken = {
        "closing_balance_paise": 999999,
        "cycles": [
            {
                "statement_date": "2025-04-14",
                "opening_paise": 0,
                "purchases_paise": 1000,
                "finance_charge_paise": 0,
                "gst_paise": 0,
                "payments_paise": 0,
                "closing_paise": 1000,
            },
        ],
    }
    with pytest.raises(ReconciliationError):
        reconcile_card_statement(broken)
