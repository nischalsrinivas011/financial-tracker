import httpx
import pytest

from app.llm.client import AllProvidersExhaustedError, complete


def _openai_response(text: str, prompt_tokens=10, completion_tokens=5) -> dict:
    return {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def all_keys_set(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")


def test_no_provider_configured_raises_immediately(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    with pytest.raises(AllProvidersExhaustedError):
        complete([{"role": "user", "content": "hi"}])


def test_first_provider_success(all_keys_set):
    def handler(request):
        assert "groq" in str(request.url)
        return httpx.Response(200, json=_openai_response("groceries"))

    result = complete([{"role": "user", "content": "hi"}], client=_mock_client(handler))

    assert result.text == "groceries"
    assert result.provider == "groq"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.latency_ms >= 0


def test_rate_limit_falls_back_to_next_provider(all_keys_set):
    def handler(request):
        if "groq" in str(request.url):
            return httpx.Response(429, json={"error": "rate limited"})
        if "generativelanguage.googleapis.com" in str(request.url):
            return httpx.Response(200, json=_openai_response("transport"))
        raise AssertionError(f"unexpected provider hit: {request.url}")

    result = complete([{"role": "user", "content": "hi"}], client=_mock_client(handler))

    assert result.provider == "gemini"
    assert result.text == "transport"


def test_all_providers_exhausted_raises(all_keys_set):
    def handler(request):
        return httpx.Response(429, json={"error": "rate limited"})

    with pytest.raises(AllProvidersExhaustedError):
        complete([{"role": "user", "content": "hi"}], client=_mock_client(handler))


def test_connection_error_falls_back(all_keys_set):
    def handler(request):
        if "groq" in str(request.url):
            raise httpx.ConnectError("connection refused")
        if "generativelanguage.googleapis.com" in str(request.url):
            return httpx.Response(200, json=_openai_response("dining"))
        raise AssertionError(f"unexpected provider hit: {request.url}")

    result = complete([{"role": "user", "content": "hi"}], client=_mock_client(handler))

    assert result.provider == "gemini"


def test_preferred_provider_is_tried_first(all_keys_set):
    def handler(request):
        assert "mistral" in str(request.url)
        return httpx.Response(200, json=_openai_response("shopping"))

    result = complete(
        [{"role": "user", "content": "hi"}],
        preferred_provider="mistral",
        client=_mock_client(handler),
    )

    assert result.provider == "mistral"


def test_provider_without_api_key_is_skipped(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    def handler(request):
        assert "groq" in str(request.url)
        return httpx.Response(200, json=_openai_response("fuel"))

    result = complete([{"role": "user", "content": "hi"}], client=_mock_client(handler))

    assert result.provider == "groq"
