# CLAUDE.md

Read this file before making any change. If a request conflicts with the rules
here, say so instead of complying.

## What this project is

A personal finance analysis app. It ingests bank and credit card statements,
extracts transactions deterministically, categorises spending, and answers
natural-language questions using hybrid retrieval (SQL over transactions +
vector search over an Indian personal-finance knowledge corpus).

Primary purpose is a portfolio artifact demonstrating retrieval architecture and
evaluation methodology. Correctness and measurability matter more than feature count.

## Hard rules — never violate

1. **Money is integers in paise.** Never floats. Never rupees as a float. Format
   to rupees only at the display layer.
2. **All timestamps IST.** Store as timezone-aware UTC, render IST.
3. **No PII leaves this server.** Redact before any external LLM call: account
   numbers (keep last 4), PAN, Aadhaar, IFSC, customer IDs, names, addresses,
   phone, email, personal UPI VPAs. Merchant VPAs may pass through.
4. **Never persist an uploaded statement.** Parse in memory, store extracted rows,
   discard the file within the request. No disk writes, no object storage.
5. **Never log statement contents.** Log IDs, counts, and durations only. No
   transaction descriptions, no balances, no account numbers in logs or errors.
6. **PDF passwords are in-memory only.** Never persisted, never logged, never in
   an exception message or stack trace.
7. **No secrets in the repo.** Everything via environment variables. If you find a
   secret in a file, stop and tell me.
8. **Synthetic data only for now.** Real statement upload is not implemented.
   Do not add it without an explicit instruction. Real upload behind Google
   auth was proposed 2026-08-09 and parked as a Phase 3/4 decision, not yet
   authorized — see `docs/DECISIONS.md`.

## Stack

- Backend: Python 3.11+, FastAPI, SQLAlchemy
- Database: Postgres with pgvector (Neon free tier)
- Frontend: Next.js (App Router), TypeScript, Tailwind
- Embeddings: sentence-transformers, run locally. Never a paid embedding API.
- LLM: free-tier providers only (Gemini Flash, Groq, Cerebras). See below.
- Tests: pytest

## LLM provider rules

- All model calls go through `app/llm/client.py`. No provider SDK is imported
  anywhere else in the codebase.
- The interface is provider-agnostic so we can swap or fall back between free tiers.
- Never add a provider that requires a credit card on file.
- Route by cost: cheap/fast model for parsing and categorisation, stronger model
  only for the chat layer. Questions answerable from SQL alone must not make a
  generative call at all.
- Every call records input tokens, output tokens, provider, and latency.

## Architecture boundaries

- **Extraction is deterministic.** Bank-specific parsers first, LLM only as a
  fallback for unrecognised formats. Never use retrieval or embeddings for
  transaction extraction.
- **Every parsed statement must reconcile**: opening + credits − debits == closing.
  On failure, flag the statement. Never surface unreconciled data as if it were valid.
- **Deduplicate** on (account_id, date, amount, normalised_description).
- **RAG is scoped to the advisory layer only** — the finance knowledge corpus.

## Testing

- The parser is test-first. Fixtures live in `tests/fixtures/` as synthetic
  statements paired with expected JSON. Write the fixture before the parser.
- Raw synthetic statement PDFs are supplied by the owner. Claude derives and
  reviews the expected JSON for each one before the parser is written against it.
- No parser change ships without a passing fixture.
- `eval/` holds the RAG evaluation harness. Golden questions are frozen — add
  questions, never soften existing ones to make a run pass.

## Working style

- One phase at a time. Do not scaffold ahead of the current task.
- Explain your design before writing non-trivial code. I need to be able to
  defend every decision in an interview.
- When you make a design choice with real alternatives, add an entry to
  `docs/DECISIONS.md`: the problem, the options, the choice, the reasoning.
- Prefer boring, readable code over clever code.
- Do not add dependencies without telling me what and why.

## Git

- Small, focused commits. Imperative mood, present tense.
- Never commit: `.env`, anything in `data/real/`, any statement file, any key.
- Do not push. I review and push myself.

## Current phase

Phase 4 — knowledge corpus, chunking, pgvector, the router, hybrid
retrieval. Phase 1 (synthetic fixtures, deterministic parsers,
reconciliation), Phase 2 (categorisation cascade, all 3 stages live), and
Phase 3 (FastAPI + Postgres + real Clerk auth + first deploy on Render,
all verified against live services) are done. Still no frontend.

The corpus content this phase writes must match the chunk ids already
named in `golden_questions.yaml`'s `relevant_chunks` fields — that file
was written before the corpus and is the source of truth for what needs
to exist, not the other way around. Phase 4 builds one working chunking
strategy end-to-end (section-aware, per the hypothesis in
`RAG_EVALUATION.md`); the 3-way chunking comparison against fixed-size
and semantic is explicitly Phase 5's job, not this one.
