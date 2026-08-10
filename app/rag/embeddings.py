"""Local embedding generation - never a paid API, per CLAUDE.md's stack rule.

Model is all-MiniLM-L6-v2 (384 dims): a deliberate tradeoff for free-tier
CPU-only deploy constraints, not the highest-quality option available -
see the 2026-08-09 "Embedding model" entry in docs/DECISIONS.md.

Runs on fastembed (ONNXRuntime), not sentence-transformers/torch: torch
alone resolves to ~360MB resident at import, which OOM-killed the app on
Render's free 512MB tier. Same model weights, ~211MB fully loaded via
ONNXRuntime instead - see the 2026-08-10 "Embedding runtime" entry in
docs/DECISIONS.md.
"""

from functools import lru_cache

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(MODEL_NAME)


def embed(text: str) -> list[float]:
    return next(iter(_model().embed([text]))).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return [v.tolist() for v in _model().embed(texts)]
