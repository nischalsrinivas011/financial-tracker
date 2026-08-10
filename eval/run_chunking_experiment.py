"""The chunking experiment: run the golden set's retrieval questions
against all three strategies and record the deltas (RAG_EVALUATION.md).

Pre-registered hypothesis (RAG_EVALUATION.md, stated before this ran):
personal-finance frameworks are highly structured, so section-aware
should beat fixed-size on recall because a rule of thumb and its
caveats/conditions live in the same section and fixed-size splits them
apart.

In-memory cosine search (numpy), not pgvector: this is a one-off
comparison over a few dozen vectors each, not a production retrieval
path - Phase 4 already chose section-aware as the live strategy
(app/rag/chunking.py, app/rag/retrieval.py), this script doesn't touch it.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

import numpy as np
import yaml

from app.rag.embeddings import embed, embed_batch
from eval.chunking_strategies import ExperimentChunk, fixed_size_chunks, section_aware_chunks, semantic_chunks

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
GOLDEN_QUESTIONS = Path(__file__).parent / "golden_questions.yaml"
RESULTS_DIR = Path(__file__).parent / "results"
K_VALUES = [3, 5, 10]


def _load_questions() -> list[dict]:
    with open(GOLDEN_QUESTIONS) as f:
        data = yaml.safe_load(f)
    return [q for q in data["questions"] if q.get("relevant_chunks")]


def _cosine(a, b) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _search(chunks: list[ExperimentChunk], embeddings: list[list[float]], query: str, k: int) -> list[ExperimentChunk]:
    query_embedding = embed(query)
    scored = sorted(
        zip(chunks, embeddings),
        key=lambda pair: -_cosine(query_embedding, pair[1]),
    )
    return [c for c, _ in scored[:k]]


def _precision_recall_at_k(retrieved: list[ExperimentChunk], relevant_ids: set[str], k: int) -> tuple[float, float]:
    top_k = retrieved[:k]

    # Precision: fraction of retrieved CHUNKS that overlap any target id.
    relevant_chunk_count = sum(1 for c in top_k if c.provenance & relevant_ids)
    precision = relevant_chunk_count / k if k else 0.0

    # Recall: fraction of target IDs covered by the union of retrieved
    # provenance - counted per distinct id, not per matching chunk, or a
    # fragmented strategy where several small chunks all trace back to the
    # same original section would over-count recall past 100%.
    covered_ids: set[str] = set()
    for c in top_k:
        covered_ids |= c.provenance & relevant_ids
    recall = len(covered_ids) / len(relevant_ids) if relevant_ids else 0.0

    return precision, recall


def _mrr(retrieved: list[ExperimentChunk], relevant_ids: set[str]) -> float:
    for rank, c in enumerate(retrieved, start=1):
        if c.provenance & relevant_ids:
            return 1.0 / rank
    return 0.0


def evaluate_strategy(chunks: list[ExperimentChunk], questions: list[dict]) -> dict:
    embeddings = embed_batch([c.content for c in chunks])

    per_question = []
    for q in questions:
        relevant_ids = set(q["relevant_chunks"])
        retrieved = _search(chunks, embeddings, q["question"], k=max(K_VALUES))
        entry = {"id": q["id"]}
        for k in K_VALUES:
            precision, recall = _precision_recall_at_k(retrieved, relevant_ids, k)
            entry[f"precision@{k}"] = precision
            entry[f"recall@{k}"] = recall
        entry["mrr"] = _mrr(retrieved, relevant_ids)
        per_question.append(entry)

    def _avg(field):
        return sum(e[field] for e in per_question) / len(per_question) if per_question else 0.0

    summary = {f"precision@{k}": _avg(f"precision@{k}") for k in K_VALUES}
    summary.update({f"recall@{k}": _avg(f"recall@{k}") for k in K_VALUES})
    summary["mrr"] = _avg("mrr")
    summary["chunk_count"] = len(chunks)

    return {"summary": summary, "per_question": per_question}


def run_experiment() -> dict:
    questions = _load_questions()

    strategies = {
        "section_aware": section_aware_chunks(KNOWLEDGE_DIR),
        "fixed_size": fixed_size_chunks(KNOWLEDGE_DIR),
        "semantic": semantic_chunks(KNOWLEDGE_DIR),
    }

    results = {name: evaluate_strategy(chunks, questions) for name, chunks in strategies.items()}

    sa_recall5 = results["section_aware"]["summary"]["recall@5"]
    fs_recall5 = results["fixed_size"]["summary"]["recall@5"]
    hypothesis_held = sa_recall5 > fs_recall5

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "questions_scored": len(questions),
        "hypothesis": (
            "section-aware should beat fixed-size on recall because a rule of thumb "
            "and its caveats live in the same section and fixed-size splits them apart"
        ),
        "hypothesis_held": hypothesis_held,
        "strategies": results,
    }


if __name__ == "__main__":
    result = run_experiment()

    RESULTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = RESULTS_DIR / f"{date_str}_chunking-experiment.json"
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"wrote {path}\n")
    print(f"Hypothesis: {result['hypothesis']}")
    print(f"Hypothesis held: {result['hypothesis_held']}\n")
    print(f"{'strategy':<15} {'chunks':>7} {'P@5':>7} {'R@5':>7} {'MRR':>7}")
    for name, r in result["strategies"].items():
        s = r["summary"]
        print(f"{name:<15} {s['chunk_count']:>7} {s['precision@5']:>7.1%} {s['recall@5']:>7.1%} {s['mrr']:>7.2f}")
