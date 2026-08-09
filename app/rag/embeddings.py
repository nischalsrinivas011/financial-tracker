"""Local embedding generation - never a paid API, per CLAUDE.md's stack rule.

Model is all-MiniLM-L6-v2 (384 dims): a deliberate tradeoff for free-tier
CPU-only deploy constraints, not the highest-quality option available -
see the 2026-08-09 "Embedding model" entry in docs/DECISIONS.md.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    return _model().encode(text, normalize_embeddings=True).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True).tolist()
