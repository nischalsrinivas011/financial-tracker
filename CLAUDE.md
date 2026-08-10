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

Phase 6 — Next.js dashboard, demo mode, deploy. Phases 1-4 are done (see
git history). Node v24.15.0 / npm 11.12.1 already installed, no setup
needed there.

Done so far in Phase 6: `POST /ask` (app/api/ask.py, wraps
app/rag/answer.py), `GET /accounts`, `GET /transactions` (+
`/transactions/summary`) — all auth-scoped, all tested
(tests/test_ask_api.py, tests/test_accounts_transactions_api.py).
CORS wired in app/main.py via `CORS_ALLOWED_ORIGINS`. `frontend/` is
scaffolded (Next.js 16 App Router, TypeScript, Tailwind v4, shadcn/ui,
Recharts) with real Clerk auth (`@clerk/nextjs`, `proxy.ts` —
Next.js 16 renamed `middleware.ts`). The dashboard
(`frontend/src/app/dashboard/page.tsx`, gated on `useAuth()`) has
upload, accounts, spending-by-category chart, transactions table, and
an ask/chat box, all built on `frontend/src/lib/api.ts`. Demo mode
(`frontend/src/app/demo/page.tsx`, linked from `/` as "Try with sample
data") needs no sign-in and no backend call — it renders
`frontend/src/data/demo-data.json`, exported from the real
arjun_salaried eval persona via `eval/export_demo_data.py` (re-run
that script if the persona's seeded data changes), with a handful of
canned Q&A pulled verbatim from the baseline eval run.

Not yet verified live: the signed-in dashboard view (upload → parse →
categorize → chart/table round-trip). Claude built and type-checked/
linted it and confirmed the signed-out redirect guard works, but
can't sign in itself — Clerk's real sign-in needs a password, which
Claude won't enter under any circumstance. Owner needs to check this
manually before it's considered done.

Not started: Vercel deploy (needs the owner's Vercel account) and
wiring the deployed frontend URL into `CORS_ALLOWED_ORIGINS` /
`CLERK_AUTHORIZED_PARTIES`.

Phase 5 (`RAG_EVALUATION.md`) is in progress. Done: `eval/` scaffolding,
`eval/seed_persona.py` (real eval user seeded via the actual upload
endpoints with arjun_salaried's data — `salaried_bengaluru_v1`), the
deterministic metrics (`eval/metrics/{routing,retrieval,constraints,cost}.py`,
no LLM needed), `eval/run_eval.py`, `eval/report.py`, and the first
baseline (`eval/results/2026-08-10_baseline.json`: routing 94.4%,
recall@5 88.0%, constraint pass rate 71.4%). `eval/FAILURES.md` has 4
real findings from reading the baseline output, not just the numbers —
one is a genuine bug (`answer_sql_question` mishandles category-less
date-range questions like "how much did I spend in February"). The
3-way chunking experiment is done too (`eval/CHUNKING_EXPERIMENT.md`):
the pre-registered hypothesis did NOT hold (fixed-size beat
section-aware on raw recall@5), but that's a corpus-size confound, not
evidence fixed-size is better — MRR (where section-aware wins) is the
more relevant metric for how this app actually uses retrieval, so
Phase 4's production choice stands.

The groundedness judge is built and run (`eval/metrics/groundedness.py`,
`eval/results/2026-08-10_groundedness-judge.json`: 18 questions, 147
claims, ~88% judge-grounded rate) but **not calibrated** —
`eval/CALIBRATION.md` (a tractable 6-question/48-claim subset) is
sitting unchecked on purpose. The owner asked Claude to fill it in
(first fully, then as an all-GROUNDED rubber stamp); both declined,
since Claude generating both the judge's verdicts and the "human"
comparison labels defeats the entire point of calibration — see the
two 2026-08-10 entries in docs/DECISIONS.md. Deferred until the owner
can test scenarios against the live app; no judge-human agreement
figure exists yet, and none should be reported until real labels do.

Not yet built: refusal-behaviour metrics (under/over-refusal rate for
`route: refuse` questions) — doesn't need human input, unblocked
whenever picked up.

Other known, deliberately deferred gaps ("we can optimize later"): the
router's 2 known misses on deliberately open-ended edge-case questions
(not chased with more keywords); vector-route retrieval at k=5 on a
21-chunk corpus sometimes pulls in tangentially-related chunks the LLM
then discusses unprompted; `sentence-transformers` pulling in ~530MB of
torch is unverified against Render's free-tier build/image size limits.
