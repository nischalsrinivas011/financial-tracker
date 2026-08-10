"""Cost and latency aggregation, per RAG_EVALUATION.md section 6.

All configured providers are free-tier (CLAUDE.md's stack rule), so
"cost" here is token counts, not a dollar figure - there is no real
dollar cost to report while the project stays on free tiers. Token
counts are still the right thing to track: they're what a paid-tier
cost would scale from, and they're a real proxy for "how much work did
each route actually do."
"""


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(int(len(sorted_values) * pct), len(sorted_values) - 1)
    return sorted_values[idx]


def evaluate_cost(call_records: list[dict]) -> dict:
    if not call_records:
        return {
            "llm_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "avg_input_tokens": 0.0,
            "avg_output_tokens": 0.0,
            "p50_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "providers_used": [],
        }

    input_tokens = sum(c["input_tokens"] for c in call_records)
    output_tokens = sum(c["output_tokens"] for c in call_records)
    latencies = sorted(c["latency_ms"] for c in call_records)
    n = len(call_records)

    return {
        "llm_calls": n,
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "avg_input_tokens": input_tokens / n,
        "avg_output_tokens": output_tokens / n,
        "p50_latency_ms": _percentile(latencies, 0.5),
        "p95_latency_ms": _percentile(latencies, 0.95),
        "providers_used": sorted({c["provider"] for c in call_records}),
    }
