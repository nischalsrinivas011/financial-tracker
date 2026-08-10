"""Phase 5 eval harness entry point.

Runs every golden question through app/rag/answer.py against the seeded
eval persona's real data (eval/seed_persona.py - run that first), collects
routing/retrieval/constraint/cost metrics, and writes a timestamped JSON
to eval/results/. Never overwrite a result - the history is the artifact
(RAG_EVALUATION.md).

Groundedness (LLM-as-judge, needs human calibration) and refusal-behaviour
metrics aren't in this pass - see docs/DECISIONS.md for why.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    # Must run before the app.db.session import chain below.
    from dotenv import load_dotenv

    load_dotenv()

import yaml

from app.db.models import User
from app.db.session import SessionLocal
from app.rag.answer import answer
from eval.metrics.constraints import evaluate_constraints
from eval.metrics.cost import evaluate_cost
from eval.metrics.retrieval import evaluate_retrieval
from eval.metrics.routing import evaluate_routing
from eval.seed_persona import EVAL_CLERK_USER_ID

GOLDEN_QUESTIONS = Path(__file__).parent / "golden_questions.yaml"
RESULTS_DIR = Path(__file__).parent / "results"


def _load_questions() -> list[dict]:
    with open(GOLDEN_QUESTIONS) as f:
        return yaml.safe_load(f)["questions"]


def _get_eval_user_id(db):
    user = db.query(User).filter_by(clerk_user_id=EVAL_CLERK_USER_ID).one_or_none()
    if user is None:
        raise RuntimeError("eval persona not seeded - run `python -m eval.seed_persona` first")
    return user.id


def run_eval(label: str) -> dict:
    questions = _load_questions()
    db = SessionLocal()
    try:
        user_id = _get_eval_user_id(db)

        answer_records = {}
        answer_texts = {}
        call_records = []
        for q in questions:
            result = answer(db, user_id, q["question"])
            answer_texts[q["id"]] = result.text
            answer_records[q["id"]] = {
                "text": result.text,
                "route": result.route,
                "used_llm": result.used_llm,
                "sources": result.sources,
                "cost": result.cost,
            }
            if result.cost:
                call_records.append(result.cost)

        routing_result = evaluate_routing(questions)
        retrieval_result = evaluate_retrieval(db, questions)
        constraints_result = evaluate_constraints(answer_texts, questions)
        cost_result = evaluate_cost(call_records)
    finally:
        db.close()

    return {
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "question_count": len(questions),
        "routing": routing_result,
        "retrieval": retrieval_result,
        "constraints": constraints_result,
        "cost": cost_result,
        "answers": answer_records,
    }


def save_result(result: dict, filename: str) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / filename
    if path.exists():
        raise FileExistsError(f"{path} already exists - never overwrite a result, the history is the artifact")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return path


if __name__ == "__main__":
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    result = run_eval(label)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = save_result(result, f"{date_str}_{label}.json")

    print(f"wrote {path}")
    print(f"routing accuracy: {result['routing']['accuracy']:.1%}")
    print(f"retrieval recall@5: {result['retrieval']['summary']['recall@5']:.1%}")
    print(f"constraint pass rate: {result['constraints']['pass_rate']:.1%}")
    cost = result["cost"]
    print(f"LLM calls: {cost['llm_calls']}, p50 latency: {cost['p50_latency_ms']:.0f}ms, p95: {cost['p95_latency_ms']:.0f}ms")
