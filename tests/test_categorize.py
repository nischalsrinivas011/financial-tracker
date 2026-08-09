import json
from pathlib import Path

import pytest

from app.categorize import cascade
from app.categorize.cascade import (
    UnresolvedCategoryError,
    categorize_bank_transaction,
    categorize_card_transaction,
)
from app.llm.client import LLMResponse

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
    # An unrecognised narration *shape* never even reaches the LLM stage:
    # normalize_bank_merchant returns None for it, and the cascade only
    # calls the LLM when it has a merchant to ask about. So this raises for
    # a structural reason, independent of whether any provider is configured.
    with pytest.raises(UnresolvedCategoryError):
        categorize_bank_transaction("SOME BRAND NEW NARRATION SHAPE NOBODY HAS SEEN", "HDFC BANK")


def test_unresolved_card_description_raises_instead_of_guessing(monkeypatch):
    # Card merchant is always non-None (normalize_card_merchant is a
    # pass-through), so this genuinely reaches the LLM stage - explicitly
    # clear provider keys so this test is deterministic regardless of
    # whether conftest.py's .env autoload finds real ones. Without this,
    # a real key present in the environment would make the LLM actually
    # resolve "SOME MERCHANT NOT IN THE LOOKUP TABLE" to something, and
    # cache the bogus result into the real llm_learned.json.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    with pytest.raises(UnresolvedCategoryError):
        categorize_card_transaction("SOME MERCHANT NOT IN THE LOOKUP TABLE")


def _fake_llm_response(text: str) -> LLMResponse:
    return LLMResponse(
        text=text, provider="groq", model="llama-3.1-8b-instant",
        input_tokens=12, output_tokens=2, latency_ms=42.0,
    )


def test_unseen_merchant_resolved_via_llm_and_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(cascade, "_LEARNED_PATH", tmp_path / "llm_learned.json")

    calls = []

    def fake_complete(messages, **kwargs):
        calls.append(messages)
        return _fake_llm_response("shopping")

    monkeypatch.setattr(cascade, "complete", fake_complete)

    result = categorize_card_transaction("SOME BRAND NEW MERCHANT XYZ")
    assert result == {"merchant": "SOME BRAND NEW MERCHANT XYZ", "category": "shopping"}
    assert len(calls) == 1

    # Second lookup for the same merchant must hit the learned cache, not the LLM again.
    result_again = categorize_card_transaction("SOME BRAND NEW MERCHANT XYZ")
    assert result_again == {"merchant": "SOME BRAND NEW MERCHANT XYZ", "category": "shopping"}
    assert len(calls) == 1

    learned = json.loads((tmp_path / "llm_learned.json").read_text())
    assert learned["card"]["SOME BRAND NEW MERCHANT XYZ"] == "shopping"


def test_llm_returning_a_category_outside_the_taxonomy_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(cascade, "_LEARNED_PATH", tmp_path / "llm_learned.json")
    monkeypatch.setattr(cascade, "complete", lambda messages, **kwargs: _fake_llm_response("not_a_real_category"))

    with pytest.raises(UnresolvedCategoryError):
        categorize_card_transaction("ANOTHER UNSEEN MERCHANT")
