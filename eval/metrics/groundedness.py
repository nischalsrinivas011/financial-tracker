"""LLM-as-judge groundedness checking, per RAG_EVALUATION.md section 3.

Decomposes an answer into atomic claims and checks each against the
context that was actually available at generation time (retrieved corpus
chunks + SQL result), via one structured LLM call using the prompt in
eval/judges/groundedness_prompt.txt.

"Use a different model than the generator where practical"
(RAG_EVALUATION.md): defaults to preferring Mistral, since Groq is
generation's primary/most-available provider in this project's fallback
order (app/llm/client.py) - not a hard guarantee (the fallback chain can
still land on Groq if Mistral is unavailable), a practical default.

Uncalibrated, this is not trustworthy on its own - see
eval/CALIBRATION.md for the human hand-labeling pass this needs before
its output means anything.
"""

import re
from pathlib import Path

from app.llm.client import AllProvidersExhaustedError, complete

PROMPT_TEMPLATE = (Path(__file__).parent.parent / "judges" / "groundedness_prompt.txt").read_text(encoding="utf-8")

_CLAIM_RE = re.compile(r"CLAIM:\s*(.+?)\s*\nGROUNDED:\s*(yes|no)", re.IGNORECASE)


def _parse_claims(judge_output: str) -> list[dict]:
    return [
        {"claim": claim.strip(), "grounded": verdict.lower() == "yes"}
        for claim, verdict in _CLAIM_RE.findall(judge_output)
    ]


def judge_groundedness(question: str, answer_text: str, context: str, preferred_provider: str = "mistral") -> dict:
    prompt = PROMPT_TEMPLATE.format(question=question, context=context, answer=answer_text)

    try:
        response = complete(
            [{"role": "user", "content": prompt}],
            preferred_provider=preferred_provider,
            max_tokens=600,
        )
    except AllProvidersExhaustedError as exc:
        return {"claims": [], "grounded_fraction": None, "error": str(exc)}

    claims = _parse_claims(response.text)
    grounded_fraction = sum(c["grounded"] for c in claims) / len(claims) if claims else None

    return {
        "claims": claims,
        "grounded_fraction": grounded_fraction,
        "judge_provider": response.provider,
        "judge_model": response.model,
        "raw_output": response.text,
    }
