import json
from pathlib import Path

import pytest

from app.parsers.hdfc_bank import parse_bank_statement
from app.parsers.reconcile import ReconciliationError, reconcile_bank_statement

FIXTURES = Path(__file__).parent / "fixtures"
PERSONAS = ["arjun_salaried", "meera_freelance", "rohit_debt", "sneha_young", "vikram_creep"]

TXN_FIELDS = ["date", "narration", "reference", "withdrawal_paise", "deposit_paise", "balance_paise"]


def load_expected(persona):
    path = FIXTURES / persona / f"{persona}_FY2025-26_bank.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("persona", PERSONAS)
def test_header_fields(persona):
    expected = load_expected(persona)
    result = parse_bank_statement(FIXTURES / persona / f"{persona}_FY2025-26_bank.pdf")

    assert result["bank"] == expected["bank"]
    assert result["account_number_masked"] == expected["account_number_masked"]
    assert result["ifsc"] == expected["ifsc"]
    assert result["period"] == expected["period"]


@pytest.mark.parametrize("persona", PERSONAS)
def test_totals(persona):
    expected = load_expected(persona)
    result = parse_bank_statement(FIXTURES / persona / f"{persona}_FY2025-26_bank.pdf")

    assert result["opening_balance_paise"] == expected["opening_balance_paise"]
    assert result["closing_balance_paise"] == expected["closing_balance_paise"]
    assert result["total_credits_paise"] == expected["total_credits_paise"]
    assert result["total_debits_paise"] == expected["total_debits_paise"]
    assert result["transaction_count"] == expected["transaction_count"]
    assert len(result["transactions"]) == expected["transaction_count"]


@pytest.mark.parametrize("persona", PERSONAS)
def test_transactions_match_fixture_exactly(persona):
    expected = load_expected(persona)
    result = parse_bank_statement(FIXTURES / persona / f"{persona}_FY2025-26_bank.pdf")

    for i, (got, want) in enumerate(zip(result["transactions"], expected["transactions"])):
        for field in TXN_FIELDS:
            assert got[field] == want[field], f"{persona} txn {i} ({want['date']}) field {field}"


@pytest.mark.parametrize("persona", PERSONAS)
def test_parsed_statement_reconciles(persona):
    result = parse_bank_statement(FIXTURES / persona / f"{persona}_FY2025-26_bank.pdf")
    reconcile_bank_statement(result)


def test_reconciliation_gate_rejects_a_broken_statement():
    broken = {
        "opening_balance_paise": 1000,
        "closing_balance_paise": 5000,
        "total_credits_paise": 2000,
        "total_debits_paise": 500,
        "transactions": [
            {"date": "2025-04-01", "deposit_paise": 2000, "withdrawal_paise": 500, "balance_paise": 2500},
        ],
    }
    with pytest.raises(ReconciliationError):
        reconcile_bank_statement(broken)
