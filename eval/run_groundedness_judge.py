"""Run the groundedness judge on the baseline's 18 LLM-synthesized answers
(all vec-*/hyb-* questions - the only ones where hallucination is
possible; sql/refuse answers are template-generated and trivially
grounded by construction, not meaningful to judge).

Uses the exact answer text already recorded in
eval/results/2026-08-10_baseline.json, not freshly regenerated - LLM
generation isn't perfectly deterministic, and calibration needs to grade
the actual answers a human will also grade, not a fresh sample that may
differ.

Context wasn't stored in baseline.json (a gap fixed going forward in
run_eval.py, not retroactively - see docs/DECISIONS.md) - reconstructed
here via search()/answer_sql_question instead. Safe because retrieval is
deterministic (same corpus, same embeddings): the context rebuilt here
matches what was actually used at generation time.

Writes two files:
  - eval/results/<date>_groundedness-judge.json: full judge output.
  - eval/CALIBRATION.md: the blind hand-labeling doc (claims only, no
    judge verdicts) for the human calibration pass.
"""

from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

import json

import yaml

from app.db.session import SessionLocal
from app.rag.retrieval import search
from app.rag.router import route as route_question
from app.rag.sql_answer import answer_sql_question
from eval.metrics.groundedness import judge_groundedness
from eval.run_eval import _get_eval_user_id

GOLDEN_QUESTIONS = Path(__file__).parent / "golden_questions.yaml"
BASELINE_PATH = Path(__file__).parent / "results" / "2026-08-10_baseline.json"
JUDGE_RESULTS_PATH = Path(__file__).parent / "results" / "2026-08-10_groundedness-judge.json"
RESULTS_DIR = Path(__file__).parent / "results"
CALIBRATION_DOC = Path(__file__).parent / "CALIBRATION.md"

# All 18 judged questions is a lot to hand-label in one sitting (147
# claims). This subset trades sample size for tractability: 3 vector + 3
# hybrid, spanning easy/medium/hard difficulty and distinct topics
# (budgeting, insurance, housing, prepay-vs-invest, savings, affordability)
# - 48 claims, not 147. A real, honest calibration sample, not a token one.
CALIBRATION_SUBSET = ["vec-001", "vec-002", "vec-005", "hyb-001", "hyb-006", "hyb-007"]


def _load_questions_by_id() -> dict:
    with open(GOLDEN_QUESTIONS) as f:
        data = yaml.safe_load(f)
    return {q["id"]: q for q in data["questions"]}


def _rebuild_context(db, user_id, question: dict) -> str:
    chunks = search(db, question["question"], k=5)
    corpus_text = "\n\n".join(f"[{c.chunk_id}] {c.heading}\n{c.content}" for c in chunks)
    if question["route"] == "hybrid":
        sql_context = answer_sql_question(db, user_id, question["question"])
        return f"User's actual data:\n{sql_context}\n\nKnowledge corpus context:\n{corpus_text}"
    return corpus_text


def run_judge_on_baseline() -> dict:
    questions_by_id = _load_questions_by_id()
    with open(BASELINE_PATH, encoding="utf-8") as f:
        baseline = json.load(f)

    # The router's ACTUAL decision at baseline time, not the golden set's
    # expected route - edge-003/edge-005 are the router's 2 known misses
    # (expected hybrid, actually routed to sql), so their baseline answers
    # are template text, not LLM output, and must not be judged as if they
    # were - router.py is deterministic and unchanged, so re-running it now
    # reconstructs the same decision the baseline run actually made.
    llm_question_ids = [
        qid for qid in baseline["answers"]
        if route_question(questions_by_id[qid]["question"]).route in ("vector", "hybrid")
    ]

    db = SessionLocal()
    try:
        user_id = _get_eval_user_id(db)
        results = {}
        for qid in llm_question_ids:
            question = questions_by_id[qid]
            answer_text = baseline["answers"][qid]
            context = _rebuild_context(db, user_id, question)
            judged = judge_groundedness(question["question"], answer_text, context)
            results[qid] = {
                "question": question["question"],
                "route": question["route"],
                "answer": answer_text,
                "context": context,
                **judged,
            }
    finally:
        db.close()

    return results


def write_calibration_doc(results: dict, subset: list[str] | None = None) -> None:
    question_ids = subset if subset is not None else list(results)
    lines = [
        "# Groundedness calibration",
        "",
        "Hand-label each claim below as GROUNDED or NOT GROUNDED against the",
        "context shown, **before** looking at the judge's verdicts (kept in a",
        "separate results file specifically so this stays blind). Edit this file",
        "in place: replace each `[ ]` with `[grounded]` or `[not grounded]`.",
        "",
        "A claim is GROUNDED only if the context directly supports it - not if it",
        "sounds plausible or matches general personal-finance knowledge.",
        "",
    ]
    if subset is not None:
        lines += [
            f"({len(subset)} of {len(results)} judged questions - a representative subset",
            "chosen for tractability, not all of them. See docs/DECISIONS.md.)",
            "",
        ]
    for qid in question_ids:
        r = results[qid]
        lines.append(f"## {qid}")
        lines.append(f"**Question:** {r['question']}")
        lines.append("")
        lines.append("<details><summary>Context (click to expand)</summary>")
        lines.append("")
        lines.append("```")
        lines.append(r["context"])
        lines.append("```")
        lines.append("</details>")
        lines.append("")
        lines.append(f"**Full answer:** {r['answer']}")
        lines.append("")
        for i, c in enumerate(r["claims"], start=1):
            lines.append(f"{i}. [ ] {c['claim']}")
        lines.append("")

    CALIBRATION_DOC.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    results = run_judge_on_baseline()

    RESULTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = RESULTS_DIR / f"{date_str}_groundedness-judge.json"
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    write_calibration_doc(results)

    total_claims = sum(len(r["claims"]) for r in results.values())
    grounded_claims = sum(sum(c["grounded"] for c in r["claims"]) for r in results.values())
    print(f"wrote {path}")
    print(f"wrote {CALIBRATION_DOC}")
    print(f"questions judged: {len(results)}, total claims: {total_claims}")
    print(f"judge grounded rate: {grounded_claims / total_claims:.1%}" if total_claims else "no claims parsed")
