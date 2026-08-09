import json
from pathlib import Path

import pytest

from app.categorize.cascade import (
    UnresolvedCategoryError,
    categorize_bank_transaction,
    categorize_card_transaction,
)

FIXTURES = Path(__file__).parent / "fixtures"
PERSONAS = ["arjun_salaried", "meera_freelance", "rohit_debt", "sneha_young", "vikram_creep"]


def load(persona, kind):
    path = FIXTURES / persona / f"{persona}_FY2025-26_{kind}.json"
    return json.loads(path.read_text())


@pytest.mark.parametrize("persona", PERSONAS)
def test_every_bank_transaction_categorizes_correctly(persona):
    bank = load(persona, "bank")
    bank_name = bank["bank"]

    for i, t in enumerate(bank["transactions"]):
        result = categorize_bank_transaction(t["narration"], bank_name)
        assert result["category"] == t["expected_category"], f"{persona} txn {i} ({t['date']})"

        if t["narration"].startswith("EMI "):
            # Known, permanent gap: the loan type isn't present anywhere in
            # the statement text (see normalize.py). Category still resolves
            # correctly from the narration shape alone; merchant can't.
            assert result["merchant"] is None
        else:
            assert result["merchant"] == t["expected_merchant"], f"{persona} txn {i} ({t['date']})"


@pytest.mark.parametrize("persona", PERSONAS)
def test_every_card_transaction_categorizes_correctly(persona):
    card = load(persona, "card")

    for i, cycle in enumerate(card["cycles"]):
        for j, t in enumerate(cycle["transactions"]):
            result = categorize_card_transaction(t["description"])
            assert result["category"] == t["expected_category"], f"{persona} cycle {i} txn {j}"
            assert result["merchant"] == t["description"]


def test_unresolved_narration_raises_instead_of_guessing():
    with pytest.raises(UnresolvedCategoryError):
        categorize_bank_transaction("SOME BRAND NEW NARRATION SHAPE NOBODY HAS SEEN", "HDFC BANK")


def test_unresolved_card_description_raises_instead_of_guessing():
    with pytest.raises(UnresolvedCategoryError):
        categorize_card_transaction("SOME MERCHANT NOT IN THE LOOKUP TABLE")
