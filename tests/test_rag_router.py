"""Router accuracy against the full golden question set. Not the formal
Phase 5 eval harness (RAG_EVALUATION.md's routing-accuracy metric with a
committed baseline.json lives there) - a lightweight sanity check that
the rule-based router (app/rag/router.py) is doing something reasonable
before building answer assembly on top of it.
"""

from collections import Counter
from pathlib import Path

import pytest
import yaml

from app.rag.router import route

GOLDEN_QUESTIONS = Path(__file__).parent.parent / "golden_questions.yaml"

# Known, understood misses: both are deliberately open-ended edge-case
# questions ("edge cases - where products actually break", per the file's
# own section header) with no specific nameable concept for a keyword
# pattern to match - they confidently match an SQL-only signal and no
# corpus signal, so they land on sql instead of hybrid. Hand-crafting
# patterns for these two exact phrases would be overfitting to the eval
# set, not building a router that generalizes. If accuracy needs to clear
# the >95% target these two represent, the documented next step is an
# LLM-based fallback for low-confidence cases, not more keywords.
KNOWN_MISSES = {"edge-003", "edge-005"}


def _load_questions():
    with open(GOLDEN_QUESTIONS) as f:
        data = yaml.safe_load(f)
    return data["questions"]


@pytest.mark.parametrize("q", _load_questions(), ids=lambda q: q["id"])
def test_router_matches_expected_route_or_is_a_known_miss(q):
    result = route(q["question"])
    if q["id"] in KNOWN_MISSES:
        assert result.route != q["route"], (
            f"{q['id']} is listed as a known miss but now routes correctly "
            "- remove it from KNOWN_MISSES"
        )
    else:
        assert result.route == q["route"], f"{q['id']}: {q['question']!r}"


def test_overall_accuracy_and_confusion_matrix():
    questions = _load_questions()
    confusion = Counter()
    correct = 0

    for q in questions:
        result = route(q["question"])
        confusion[(q["route"], result.route)] += 1
        if result.route == q["route"]:
            correct += 1

    accuracy = correct / len(questions)
    assert accuracy >= 0.90, f"router accuracy dropped below 90%: {accuracy:.1%}"

    # The two known misses account for exactly the gap between measured
    # accuracy and the full set - if this assertion breaks, something
    # changed beyond the two documented cases.
    assert correct == len(questions) - len(KNOWN_MISSES)
