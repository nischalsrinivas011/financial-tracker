import eval.metrics.groundedness as groundedness_module
from app.llm.client import AllProvidersExhaustedError, LLMResponse
from eval.metrics.groundedness import _parse_claims, judge_groundedness


def test_parse_claims_extracts_claim_and_verdict_pairs():
    raw = (
        "CLAIM: The 50/30/20 rule allocates 50% to needs\n"
        "GROUNDED: yes\n"
        "CLAIM: You should always follow this rule exactly\n"
        "GROUNDED: no\n"
    )
    claims = _parse_claims(raw)
    assert claims == [
        {"claim": "The 50/30/20 rule allocates 50% to needs", "grounded": True},
        {"claim": "You should always follow this rule exactly", "grounded": False},
    ]


def test_parse_claims_handles_no_claims():
    assert _parse_claims("no claims here, malformed output") == []


def _fake_response(text):
    return LLMResponse(text=text, provider="mistral", model="open-mistral-nemo",
                        input_tokens=100, output_tokens=30, latency_ms=200.0)


def test_judge_groundedness_computes_fraction(monkeypatch):
    raw = "CLAIM: a\nGROUNDED: yes\nCLAIM: b\nGROUNDED: no\nCLAIM: c\nGROUNDED: yes\n"
    monkeypatch.setattr(groundedness_module, "complete", lambda *a, **k: _fake_response(raw))

    result = judge_groundedness("q", "a b c", "context")
    assert result["grounded_fraction"] == 2 / 3
    assert len(result["claims"]) == 3
    assert result["judge_provider"] == "mistral"


def test_judge_prefers_mistral_by_default(monkeypatch):
    captured = {}

    def fake_complete(messages, **kwargs):
        captured.update(kwargs)
        return _fake_response("CLAIM: x\nGROUNDED: yes\n")

    monkeypatch.setattr(groundedness_module, "complete", fake_complete)
    judge_groundedness("q", "a", "context")
    assert captured["preferred_provider"] == "mistral"


def test_judge_returns_none_fraction_when_all_providers_unavailable(monkeypatch):
    def raise_exhausted(*a, **k):
        raise AllProvidersExhaustedError("none configured")

    monkeypatch.setattr(groundedness_module, "complete", raise_exhausted)
    result = judge_groundedness("q", "a", "context")
    assert result["grounded_fraction"] is None
    assert result["claims"] == []
