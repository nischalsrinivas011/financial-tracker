"""The categorisation cascade: rules -> merchant lookup table -> LLM for the
unseen tail, cached back.

Stage 3 (LLM) is only reached when neither a structural rule nor the
curated merchant_lookup.json resolves a merchant - the "unseen tail". A
previously-LLM-resolved merchant is served from llm_learned.json without
another call. llm_learned.json is kept separate from merchant_lookup.json
on purpose: one is human-curated, the other is model-inferred and unverified,
and that distinction should stay visible rather than get merged away.

If the LLM stage itself is unavailable (no provider configured, or every
configured provider failed) or returns something outside the known category
taxonomy, this raises UnresolvedCategoryError rather than guessing - nothing
is ever categorised on a fallback default.
"""

import json
from pathlib import Path

from app.categorize.normalize import normalize_bank_merchant, normalize_card_merchant
from app.categorize.rules import apply_bank_rules, apply_card_rules
from app.categorize.taxonomy import BANK_CATEGORIES, CARD_CATEGORIES
from app.llm.client import AllProvidersExhaustedError, complete

_LOOKUP = json.loads((Path(__file__).parent / "merchant_lookup.json").read_text())
_LEARNED_PATH = Path(__file__).parent / "llm_learned.json"


class UnresolvedCategoryError(Exception):
    """Neither a structural rule, the merchant lookup table, the learned
    cache, nor the LLM stage could categorise this transaction.
    """


def _load_learned() -> dict:
    if _LEARNED_PATH.exists():
        return json.loads(_LEARNED_PATH.read_text())
    return {"bank": {}, "card": {}}


def _save_learned(learned: dict) -> None:
    _LEARNED_PATH.write_text(json.dumps(learned, indent=2, sort_keys=True) + "\n")


def _resolve_via_llm(merchant: str, categories: list[str]) -> str:
    prompt = (
        "Classify this Indian bank/credit-card transaction merchant into exactly one category.\n"
        f"Merchant: {merchant}\n"
        f"Valid categories: {', '.join(categories)}\n"
        "Reply with only the category name, nothing else."
    )
    try:
        response = complete([{"role": "user", "content": prompt}], max_tokens=20)
    except AllProvidersExhaustedError as exc:
        raise UnresolvedCategoryError(f"LLM stage unavailable for merchant {merchant!r}: {exc}") from exc

    category = response.text.strip().lower()
    if category not in categories:
        raise UnresolvedCategoryError(
            f"LLM returned {category!r} for merchant {merchant!r}, which isn't in the known taxonomy"
        )
    return category


def categorize_bank_transaction(narration: str, bank_name: str) -> dict:
    merchant = normalize_bank_merchant(narration, bank_name)

    category = apply_bank_rules(narration, merchant)

    if category is None and merchant is not None:
        category = _LOOKUP["bank"].get(merchant)

    learned = None
    if category is None and merchant is not None:
        learned = _load_learned()
        category = learned["bank"].get(merchant)

    if category is None and merchant is not None:
        category = _resolve_via_llm(merchant, BANK_CATEGORIES)
        learned = learned or _load_learned()
        learned["bank"][merchant] = category
        _save_learned(learned)

    if category is None:
        raise UnresolvedCategoryError(f"bank narration not resolved: {narration!r}")

    return {"merchant": merchant, "category": category}


def categorize_card_transaction(description: str) -> dict:
    merchant = normalize_card_merchant(description)

    category = apply_card_rules(description)

    if category is None:
        category = _LOOKUP["card"].get(merchant)

    learned = None
    if category is None:
        learned = _load_learned()
        category = learned["card"].get(merchant)

    if category is None:
        category = _resolve_via_llm(merchant, CARD_CATEGORIES)
        learned = learned or _load_learned()
        learned["card"][merchant] = category
        _save_learned(learned)

    if category is None:
        raise UnresolvedCategoryError(f"card description not resolved: {description!r}")

    return {"merchant": merchant, "category": category}
