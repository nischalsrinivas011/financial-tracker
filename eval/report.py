"""results/*.json -> the markdown table for the README, per
RAG_EVALUATION.md's "What to publish" section.

Groundedness, judge-human agreement, and under/over-refusal rows are
"pending" until the LLM-judge pipeline exists and is calibrated (needs a
human hand-labeling pass - see docs/DECISIONS.md) - shown as pending
rather than silently omitted, so the table's shape always matches what
RAG_EVALUATION.md says should be published, even before every row has
real data.
"""

import json
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

PENDING = "pending"


def _fmt_pct(x) -> str:
    return f"{x:.1%}"


def _fmt_ms(x) -> str:
    return f"{x:.0f}ms"


def load_result(filename: str) -> dict:
    with open(RESULTS_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def render_table(baseline: dict, current: dict | None = None) -> str:
    current = current or baseline
    rows = [
        ("Routing accuracy", _fmt_pct(baseline["routing"]["accuracy"]), _fmt_pct(current["routing"]["accuracy"])),
        (
            "Recall@5",
            _fmt_pct(baseline["retrieval"]["summary"]["recall@5"]),
            _fmt_pct(current["retrieval"]["summary"]["recall@5"]),
        ),
        ("Groundedness", PENDING, PENDING),
        ("Judge-human agreement", PENDING, PENDING),
        ("Under-refusal rate", PENDING, PENDING),
        ("Over-refusal rate", PENDING, PENDING),
        (
            "Constraint pass rate",
            _fmt_pct(baseline["constraints"]["pass_rate"]),
            _fmt_pct(current["constraints"]["pass_rate"]),
        ),
        ("LLM calls per run", str(baseline["cost"]["llm_calls"]), str(current["cost"]["llm_calls"])),
        ("p50 latency", _fmt_ms(baseline["cost"]["p50_latency_ms"]), _fmt_ms(current["cost"]["p50_latency_ms"])),
        ("p95 latency", _fmt_ms(baseline["cost"]["p95_latency_ms"]), _fmt_ms(current["cost"]["p95_latency_ms"])),
    ]
    lines = ["| Metric | Baseline | Current |", "|---|---|---|"]
    lines += [f"| {label} | {b} | {c} |" for label, b, c in rows]
    return "\n".join(lines)


if __name__ == "__main__":
    baseline_file = sys.argv[1] if len(sys.argv) > 1 else None
    current_file = sys.argv[2] if len(sys.argv) > 2 else None

    if baseline_file is None:
        files = sorted(RESULTS_DIR.glob("*.json"))
        if not files:
            print("no results found in eval/results/")
            sys.exit(1)
        baseline_file = files[0].name

    baseline = load_result(baseline_file)
    current = load_result(current_file) if current_file else None
    print(render_table(baseline, current))
