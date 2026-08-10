from eval.metrics.cost import evaluate_cost


def test_empty_call_list_returns_zeroed_summary():
    result = evaluate_cost([])
    assert result["llm_calls"] == 0
    assert result["total_input_tokens"] == 0


def test_aggregates_tokens_and_providers():
    calls = [
        {"provider": "groq", "input_tokens": 40, "output_tokens": 10, "latency_ms": 100.0},
        {"provider": "groq", "input_tokens": 60, "output_tokens": 20, "latency_ms": 200.0},
        {"provider": "mistral", "input_tokens": 50, "output_tokens": 15, "latency_ms": 300.0},
    ]
    result = evaluate_cost(calls)

    assert result["llm_calls"] == 3
    assert result["total_input_tokens"] == 150
    assert result["total_output_tokens"] == 45
    assert result["avg_input_tokens"] == 50.0
    assert result["providers_used"] == ["groq", "mistral"]


def test_p95_latency_is_near_the_high_end():
    calls = [{"provider": "groq", "input_tokens": 1, "output_tokens": 1, "latency_ms": float(i)} for i in range(1, 101)]
    result = evaluate_cost(calls)
    assert result["p95_latency_ms"] >= 90.0
    assert result["p50_latency_ms"] >= 40.0
