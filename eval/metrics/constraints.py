"""Mechanical must_mention / must_not_mention checks, per RAG_EVALUATION.md
section 4. No LLM needed - cheap, fast, safe to run on every commit.
"""


def check_constraints(answer_text: str, question: dict) -> dict:
    text = answer_text.lower()
    must_mention = question.get("must_mention") or []
    must_not_mention = question.get("must_not_mention") or []

    missing = [term for term in must_mention if term.lower() not in text]
    forbidden_present = [term for term in must_not_mention if term.lower() in text]

    return {
        "id": question["id"],
        "passed": not missing and not forbidden_present,
        "missing_required": missing,
        "forbidden_present": forbidden_present,
    }


def evaluate_constraints(answers: dict[str, str], questions: list[dict]) -> dict:
    checkable = [q for q in questions if q.get("must_mention") or q.get("must_not_mention")]
    per_question = [check_constraints(answers[q["id"]], q) for q in checkable]

    passed = sum(1 for r in per_question if r["passed"])
    total = len(per_question)
    return {
        "passed": passed,
        "total": total,
        "pass_rate": passed / total if total else 0.0,
        "per_question": per_question,
    }
