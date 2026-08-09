"""Provider-agnostic LLM client with automatic fallback across free tiers.

All configured providers expose an OpenAI-compatible chat-completions
endpoint, so this is one generic HTTP client rather than one vendor SDK
per provider. No provider SDK is imported anywhere in this codebase, here
or elsewhere.

Providers are tried in PROVIDERS order; on a rate limit (HTTP 429) or a
connection failure, the next one is tried. A provider with no API key set
in the environment is skipped rather than attempted. This order is also
what a future per-user provider picker (not built yet - no UI exists in
this project) would need to default to and let a user override; each
Provider carries the metadata (trains_on_free_tier_inputs, privacy_note)
that picker would display.

Provider order rationale, verified against each provider's own site/docs
in August 2026 rather than assumed: Groq does not train on free-tier
inputs; Gemini and Mistral do, by default, unless opted out. Cerebras was
evaluated (also doesn't train on inputs, per its own site) and would have
been tried first alongside Groq, but is not included - the project owner
was unable to obtain an API key for it. Not a privacy or quality judgment
against Cerebras; see docs/DECISIONS.md.
"""

import os
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class Provider:
    name: str
    base_url: str
    model: str
    api_key_env: str
    trains_on_free_tier_inputs: bool
    privacy_note: str


PROVIDERS: list[Provider] = [
    Provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        api_key_env="GROQ_API_KEY",
        trains_on_free_tier_inputs=False,
        privacy_note="Groq does not train on free-tier API inputs.",
    ),
    Provider(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        model="gemini-2.0-flash-lite",
        api_key_env="GEMINI_API_KEY",
        trains_on_free_tier_inputs=True,
        privacy_note="Gemini's free tier may train on inputs by default.",
    ),
    Provider(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        model="open-mistral-nemo",
        api_key_env="MISTRAL_API_KEY",
        trains_on_free_tier_inputs=True,
        privacy_note="Mistral's free tier trains on inputs by default unless you opt out.",
    ),
]


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float


class AllProvidersExhaustedError(Exception):
    """Every configured, available provider failed, or none had an API key set."""


def _configured_providers(preferred_provider: str | None) -> list[Provider]:
    available = [p for p in PROVIDERS if os.environ.get(p.api_key_env)]
    if preferred_provider:
        available = sorted(available, key=lambda p: p.name != preferred_provider)
    return available


def complete(
    messages: list[dict],
    *,
    preferred_provider: str | None = None,
    max_tokens: int = 200,
    timeout: float = 15.0,
    client: httpx.Client | None = None,
) -> LLMResponse:
    providers = _configured_providers(preferred_provider)
    if not providers:
        raise AllProvidersExhaustedError("no provider has an API key set")

    owns_client = client is None
    http_client = client or httpx.Client(timeout=timeout)
    errors = []

    try:
        for provider in providers:
            api_key = os.environ[provider.api_key_env]
            start = time.monotonic()
            try:
                response = http_client.post(
                    f"{provider.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": provider.model, "messages": messages, "max_tokens": max_tokens},
                )
            except httpx.RequestError as exc:
                errors.append(f"{provider.name}: connection error ({exc})")
                continue

            latency_ms = (time.monotonic() - start) * 1000

            if response.status_code == 429:
                errors.append(f"{provider.name}: rate limited (429)")
                continue
            if response.status_code >= 400:
                errors.append(f"{provider.name}: HTTP {response.status_code}")
                continue

            data = response.json()
            usage = data.get("usage", {})
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                provider=provider.name,
                model=provider.model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=latency_ms,
            )
    finally:
        if owns_client:
            http_client.close()

    raise AllProvidersExhaustedError("; ".join(errors))
