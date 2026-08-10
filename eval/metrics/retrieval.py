"""Retrieval precision/recall@k and MRR, per RAG_EVALUATION.md section 2.

Only meaningful for questions with a non-empty relevant_chunks - sql and
refuse questions never fire vector search, so they're excluded from
scoring rather than counted as automatic failures.
"""

from sqlalchemy.orm import Session

from app.rag.retrieval import search

K_VALUES = [3, 5, 10]


def _precision_recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> tuple[float, float]:
    top_k = retrieved_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    precision = hits / k if k else 0.0
    recall = hits / len(relevant_ids) if relevant_ids else 0.0
    return precision, recall


def _mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, cid in enumerate(retrieved_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def evaluate_retrieval(db: Session, questions: list[dict]) -> dict:
    scored_questions = [q for q in questions if q.get("relevant_chunks")]
    per_question = []

    for q in scored_questions:
        relevant_ids = set(q["relevant_chunks"])
        results = search(db, q["question"], k=max(K_VALUES))
        retrieved_ids = [r.chunk_id for r in results]

        entry = {"id": q["id"], "retrieved": retrieved_ids, "relevant": sorted(relevant_ids)}
        for k in K_VALUES:
            precision, recall = _precision_recall_at_k(retrieved_ids, relevant_ids, k)
            entry[f"precision@{k}"] = precision
            entry[f"recall@{k}"] = recall
        entry["mrr"] = _mrr(retrieved_ids, relevant_ids)
        per_question.append(entry)

    def _avg(field):
        return sum(e[field] for e in per_question) / len(per_question) if per_question else 0.0

    summary = {f"precision@{k}": _avg(f"precision@{k}") for k in K_VALUES}
    summary.update({f"recall@{k}": _avg(f"recall@{k}") for k in K_VALUES})
    summary["mrr"] = _avg("mrr")
    summary["questions_scored"] = len(per_question)

    return {"summary": summary, "per_question": per_question}
