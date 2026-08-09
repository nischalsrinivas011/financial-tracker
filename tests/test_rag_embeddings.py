"""Real embedding model, not mocked - same philosophy as the rest of this
suite (real Neon, real PDFs, real Clerk SDK). Downloads the ~80MB model
from HuggingFace on first run only; cached locally after that.
"""

import numpy as np

from app.db.models import EMBEDDING_DIM
from app.rag.embeddings import embed, embed_batch


def _cosine(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def test_embed_returns_correct_dimensionality():
    vec = embed("How much should I keep in an emergency fund?")
    assert len(vec) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in vec)


def test_similar_sentences_are_closer_than_dissimilar_ones():
    emergency_fund_q = embed("How much emergency fund should I keep?")
    emergency_fund_related = embed("What's a safe amount of savings to hold for a job loss?")
    unrelated = embed("How does a SIP work?")

    assert _cosine(emergency_fund_q, emergency_fund_related) > _cosine(emergency_fund_q, unrelated)


def test_embed_batch_matches_individual_embed():
    texts = ["credit utilization ratio", "rent versus buy a home"]
    batch = embed_batch(texts)
    individual = [embed(t) for t in texts]

    assert len(batch) == 2
    for b, i in zip(batch, individual):
        assert _cosine(b, i) > 0.999  # same model/input, should be ~identical
