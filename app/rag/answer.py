"""Top-level answer assembly: route a question, then produce an answer.

sql route never calls the LLM (CLAUDE.md rule - answer_sql_question is
pure computation). vector/hybrid use the LLM client's default (stronger)
tier to synthesize a cited answer from retrieved corpus chunks, plus SQL
context for hybrid. If every configured provider fails, falls back to
returning the raw retrieved chunks rather than surfacing an error -
degraded, not broken.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.llm.client import AllProvidersExhaustedError, complete
from app.rag.retrieval import search
from app.rag.router import route
from app.rag.sql_answer import answer_sql_question

REFUSAL_MESSAGE = (
    "I can't help with that one - it's outside what this app can responsibly answer "
    "from your data or general financial guidance."
)

_SYSTEM_INSTRUCTIONS = (
    "Answer the user's personal-finance question using ONLY the context provided below. "
    "Cite which chunk_id(s) you drew from in square brackets. Present trade-offs rather "
    "than directive advice ('you should definitely...'). Do not invent numbers that aren't "
    "in the context."
)


@dataclass
class Answer:
    text: str
    route: str
    used_llm: bool
    sources: list[str] = field(default_factory=list)
    # Per CLAUDE.md: every LLM call records tokens/provider/latency. None
    # when no call was made (sql/refuse, or every provider unavailable).
    cost: dict | None = None


def _synthesize(question: str, chunks, sql_context: str | None) -> tuple[str, bool, dict | None]:
    corpus_text = "\n\n".join(f"[{c.chunk_id}] {c.heading}\n{c.content}" for c in chunks)
    parts = [_SYSTEM_INSTRUCTIONS, "", f"Question: {question}"]
    if sql_context:
        parts += ["", "User's actual data:", sql_context]
    parts += ["", "Knowledge corpus context:", corpus_text]

    try:
        response = complete([{"role": "user", "content": "\n".join(parts)}], max_tokens=400)
        cost = {
            "provider": response.provider,
            "model": response.model,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "latency_ms": response.latency_ms,
        }
        return response.text, True, cost
    except AllProvidersExhaustedError:
        # Degraded, not broken: surface what was retrieved instead of an error.
        fallback = sql_context + "\n\n" if sql_context else ""
        fallback += "\n\n".join(f"{c.heading}: {c.content}" for c in chunks)
        return fallback, False, None


def answer(db: Session, user_id: uuid.UUID, question: str) -> Answer:
    result = route(question)

    if result.route == "refuse":
        return Answer(text=REFUSAL_MESSAGE, route="refuse", used_llm=False)

    if result.route == "sql":
        text = answer_sql_question(db, user_id, question)
        return Answer(text=text, route="sql", used_llm=False)

    if result.route == "vector":
        chunks = search(db, question, k=5)
        text, used_llm, cost = _synthesize(question, chunks, sql_context=None)
        return Answer(text=text, route="vector", used_llm=used_llm, sources=[c.chunk_id for c in chunks], cost=cost)

    # hybrid
    chunks = search(db, question, k=5)
    sql_context = answer_sql_question(db, user_id, question)
    text, used_llm, cost = _synthesize(question, chunks, sql_context=sql_context)
    return Answer(text=text, route="hybrid", used_llm=used_llm, sources=[c.chunk_id for c in chunks], cost=cost)
