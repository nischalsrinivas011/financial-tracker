from eval.report import render_table

_FAKE_RESULT = {
    "routing": {"accuracy": 0.944},
    "retrieval": {"summary": {"recall@5": 0.88}},
    "constraints": {"pass_rate": 0.714},
    "cost": {"llm_calls": 18, "p50_latency_ms": 2897.0, "p95_latency_ms": 4239.0},
}


def test_renders_all_metrics_from_rag_evaluation_publish_table():
    table = render_table(_FAKE_RESULT)
    for label in ["Routing accuracy", "Recall@5", "Groundedness", "Judge-human agreement",
                  "Under-refusal rate", "Over-refusal rate", "Constraint pass rate"]:
        assert label in table


def test_pending_metrics_are_marked_pending_not_omitted():
    table = render_table(_FAKE_RESULT)
    assert "| Groundedness | pending | pending |" in table


def test_formats_real_numbers_correctly():
    table = render_table(_FAKE_RESULT)
    assert "94.4%" in table
    assert "88.0%" in table
    assert "71.4%" in table
    assert "2897ms" in table
