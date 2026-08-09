"""The categorisation cascade: rules -> merchant lookup table -> (unbuilt) LLM.

Stage 3, the LLM fallback for merchants neither stage 1 nor 2 resolves, is
deliberately not implemented yet - see the 2026-08-09 "Categorisation
cascade" entry in docs/DECISIONS.md. UnresolvedCategoryError marks exactly
the gap that stage would fill; today it's raised instead of silently
guessing, so nothing is ever mis-categorised as a side effect of missing
data.
"""

import json
from pathlib import Path

from app.categorize.normalize import normalize_bank_merchant, normalize_card_merchant
from app.categorize.rules import apply_bank_rules, apply_card_rules

_LOOKUP = json.loads((Path(__file__).parent / "merchant_lookup.json").read_text())


class UnresolvedCategoryError(Exception):
    """Neither a structural rule nor the merchant lookup table could
    categorise this transaction. This is the "unseen tail" the LLM stage of
    the cascade is meant to handle; it doesn't exist yet, so this is raised
    instead of guessing.
    """


def categorize_bank_transaction(narration: str, bank_name: str) -> dict:
    merchant = normalize_bank_merchant(narration, bank_name)

    category = apply_bank_rules(narration, merchant)
    if category is None and merchant is not None:
        category = _LOOKUP["bank"].get(merchant)

    if category is None:
        raise UnresolvedCategoryError(f"bank narration not resolved: {narration!r}")

    return {"merchant": merchant, "category": category}


def categorize_card_transaction(description: str) -> dict:
    merchant = normalize_card_merchant(description)

    category = apply_card_rules(description)
    if category is None:
        category = _LOOKUP["card"].get(merchant)

    if category is None:
        raise UnresolvedCategoryError(f"card description not resolved: {description!r}")

    return {"merchant": merchant, "category": category}
