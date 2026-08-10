"""Retrieval sanity checks against the real, already-ingested corpus in
Neon. This is not the formal eval harness (precision@k/recall@k/MRR are
Phase 5's job, per RAG_EVALUATION.md) - just confirms the pipeline
actually retrieves the right chunk for an unambiguous query before
anything else gets built on top of it.
"""

import pytest

from app.rag.retrieval import search

OBVIOUS_QUERIES = [
    ("What is the 50/30/20 budgeting rule?", "budgeting-50-30-20"),
    # Known accepted miss since the fastembed/ONNXRuntime swap (see the
    # 2026-08-10 "Embedding runtime" entry in docs/DECISIONS.md): this
    # query now ranks essential-vs-discretionary first (distance 0.522)
    # ahead of emergency-fund-framework (0.563) - a narrow margin between
    # two adjacent, genuinely related chunks in the same doc, not a
    # nonsensical result. recall@5 in eval/results is unaffected. Left
    # failing rather than loosened, same as the router's known misses.
    ("How much emergency fund should someone keep?", "emergency-fund-framework"),
    ("What happens if I miss a credit card payment?", "cc-late-payment"),
    ("How does a SIP actually work?", "sip-mechanics"),
    ("Is it better to rent or buy a home?", "rent-vs-buy"),
    ("What's the difference between the debt snowball and avalanche methods?", "debt-payoff-strategies"),
    ("How does credit utilization affect my credit score?", "credit-utilization-ratio"),
    ("Where should I park money I'll need in 6 months?", "parking-short-term-funds"),
]


@pytest.mark.parametrize("query,expected_chunk_id", OBVIOUS_QUERIES)
def test_obvious_query_retrieves_expected_chunk_at_top(db_session, query, expected_chunk_id):
    results = search(db_session, query, k=3)

    assert len(results) == 3
    assert results[0].chunk_id == expected_chunk_id, (
        f"query {query!r} top result was {results[0].chunk_id!r}, expected {expected_chunk_id!r}"
    )


def test_results_are_ranked_by_ascending_distance(db_session):
    results = search(db_session, "How should I think about paying off multiple debts?", k=5)

    distances = [r.distance for r in results]
    assert distances == sorted(distances)


def test_k_limits_result_count(db_session):
    assert len(search(db_session, "budgeting", k=1)) == 1
    assert len(search(db_session, "budgeting", k=10)) == 10
