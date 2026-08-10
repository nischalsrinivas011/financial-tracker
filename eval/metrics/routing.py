"""Routing accuracy + confusion matrix, per RAG_EVALUATION.md section 1."""

from collections import Counter

from app.rag.router import route


def evaluate_routing(questions: list[dict]) -> dict:
    confusion = Counter()
    correct = 0
    per_question = []

    for q in questions:
        result = route(q["question"])
        expected = q["route"]
        got = result.route
        is_correct = got == expected
        confusion[(expected, got)] += 1
        correct += int(is_correct)
        per_question.append({"id": q["id"], "expected": expected, "got": got, "correct": is_correct})

    total = len(questions)
    return {
        "accuracy": correct / total if total else 0.0,
        "correct": correct,
        "total": total,
        "confusion_matrix": {f"{exp}->{got}": n for (exp, got), n in sorted(confusion.items())},
        "per_question": per_question,
    }
