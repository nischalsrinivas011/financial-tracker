# Project brief

Context for anyone (human or agent) picking this up. `CLAUDE.md` holds the rules;
this file holds the reasoning and the roadmap. Read both.

## Goal

Two goals, in priority order:

1. **Portfolio artifact for AI Product Manager roles.** The thing being demonstrated
   is judgment about retrieval architecture and the ability to measure quality in a
   probabilistic system — not feature count, not visual polish.
2. **Solve a real problem.** Existing finance apps require manual expense tagging,
   which is why people abandon them. Statement upload should remove that.

Deployed web app. Not a mobile app. Play Store is explicitly out of scope and may
be revisited in six months with real usage data.

## Hard constraint: zero rupees

No paid services. No credit card on a file anywhere. This is non-negotiable and
shapes several decisions below.

- Hosting: Vercel (frontend), Render (Python API), Neon (Postgres + pgvector) — all free tiers
- Auth: Clerk or Supabase Auth free tier
- Embeddings: sentence-transformers, run locally — never a paid embedding API
- LLM: free-tier providers only (Gemini Flash ~1,500 req/day, Groq, Cerebras, Mistral)

Caveat that drove an architecture decision: Gemini's free tier may train on inputs.
Groq's does not. This is why the redaction layer is load-bearing rather than a
nice-to-have — nothing identifying may reach any provider.

Free tiers change. Model calls are isolated behind one client module so providers
can be swapped without touching application code.

## Why RAG is scoped the way it is

Naive RAG over statements would be wrong, and knowing why is part of the point.
Retrieval is lossy and non-exhaustive by design: if a statement has 340 transactions
and retrieval returns the 12 most similar chunks, the totals are silently incorrect
and nothing reconciles.

So the system splits in two:

- **Extraction is deterministic.** Bank-specific parsers, table extraction, an
  arithmetic reconciliation gate. No embeddings, no retrieval, no similarity search.
- **The advisory layer is hybrid retrieval.** SQL over the user's transactions for
  their actual numbers, plus vector search over an Indian personal-finance corpus
  (tax regimes, 80C/80D, HRA, LTCG, PPF, NPS, prepay-vs-invest, emergency funds).
  Both assembled into one grounded, cited answer.

A question like "should I prepay my home loan or invest?" needs both halves. A
question like "how much did I spend on food in March?" needs neither — it should
never reach a generative model. The router that makes that call is both a quality
mechanism and the primary cost control.

## Synthetic data only

Real statement upload is **not implemented and should not be added** without an
explicit instruction. Reasons: DPDP Act exposure (financial data is high-sensitivity;
full compliance obligations land May 2027), free-tier providers that may train on
inputs, and the fact that no recruiter will upload a bank statement to an unknown
site anyway.

Build a synthetic statement generator instead. It produces test fixtures, demo
content, and RAG eval inputs from one piece of work.

**Five demo personas, varied by financial situation rather than by bank** — the demo
should show the *analysis* differing, not just the parsing:

1. Salaried Bengaluru tech worker, heavy SIPs, healthy savings rate
2. Freelancer with irregular monthly income
3. Revolving credit card debt, paying significant finance charges
4. Young saver, no emergency fund, low insurance cover
5. High earner with lifestyle creep and a thin savings rate

## Demo mode is a first-class feature

Sceptical visitors will not sign up. A "Try with sample data" path must load a
pre-populated persona instantly, reading pre-computed JSON from the frontend with
no backend call — free-tier hosting spins down when idle, and a recruiter watching
a 45-second cold start is the worst possible outcome. Also add a cron ping to keep
the API warm.

Stretch goal (Phase 6, not yet built): let a visitor upload their *own* synthetic
statement instead of only picking a canned persona, so a hiring manager can watch
the real extraction + reconciliation pipeline run on a file they control. This
reuses the same in-memory, never-persisted upload path the app already needs —
it is not the real-statement-upload question tracked in `docs/DECISIONS.md`,
because the input stays synthetic. Design it when Phase 6 starts.

## What actually gets evaluated

`eval/` is the centrepiece, not a side quest. See `RAG_EVALUATION.md`.

Tracked: routing accuracy, retrieval precision/recall@k, groundedness via a
calibrated LLM judge, constraint adherence, under- and over-refusal rates, cost per
query, p95 latency. Baseline committed before any tuning; every change reported as
a delta.

Deliverables that matter more than the app: a results table in the README, a
documented chunking experiment (including whether the stated hypothesis held), and
an honest failure log.

## Roadmap

| Phase | Scope |
|---|---|
| 1 | Synthetic statement generator; deterministic parser; reconciliation gate; pytest fixtures. CLI only. |
| 2 | Merchant normalisation and the categorisation cascade (rules → lookup table → LLM for the unseen tail, cached back). |
| 3 | FastAPI + Postgres + auth. First deploy. |
| 4 | Knowledge corpus, chunking, pgvector, the router, hybrid retrieval. |
| 5 | Eval harness, baseline run, chunking experiment. |
| 6 | Next.js dashboard, demo mode, deploy. |
| 7 | README, decision log, eval write-up. |

Phases 2 and 5 are where the portfolio value concentrates. Phase 1 is unglamorous
and is the phase most likely to get abandoned — it is also what makes everything
after it work.

## Working agreement

The owner is new to this stack. Code that gets merged must be code the owner can
explain out loud in an interview — that is a hard filter, not an aspiration.
Explain design choices before implementing them, and log real decisions with their
alternatives in `docs/DECISIONS.md`.
