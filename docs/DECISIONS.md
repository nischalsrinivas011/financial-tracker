# Decisions log

Real design decisions with alternatives, logged as they're made. See
`CLAUDE.md` for the rules these decisions produced, and `PROJECT_BRIEF.md`
for the roadmap they slot into.

## 2026-08-09 — Real statement upload behind Google auth: parked, not decided

**Problem:** Proposal to let users who sign in with Google upload their real
bank statements, instead of the app staying synthetic-data-only.

**Options considered:**
1. Stay synthetic-only through the whole build (current default per
   `PROJECT_BRIEF.md`).
2. Add real upload now, gated behind auth.
3. Add real upload later, once auth exists (Phase 3+) and the compliance/
   security story for it has been designed on purpose rather than folded
   into an unrelated task.

**Choice:** Option 3 — deferred, revisit at Phase 3/4.

**Reasoning:** Auth doesn't exist yet (Phase 3), so there's nothing to gate
upload behind today. Real financial documents raise the stakes on rules that
are currently "good practice" into "the legal defense": never-persist (rule 4),
PII redaction before any LLM call (rule 3), DPDP Act exposure ahead of the
May 2027 compliance deadline. Deciding this properly means designing the
storage boundary, threat model, and redaction guarantees on purpose — not
deciding it as a side effect of a scope message mid-Phase-1. Revisit when
Phase 3 (auth) starts, with options and a real recommendation.

## 2026-08-09 — Synthetic statement fixtures: owner supplies raw PDFs

**Problem:** `PROJECT_BRIEF.md` originally scoped Phase 1 to include building
a synthetic statement generator. The owner offered to supply raw statement
PDFs directly instead.

**Options considered:**
1. Build a generator that produces synthetic statements programmatically
   (original plan).
2. Owner supplies raw synthetic PDFs per bank/persona; Claude derives and
   reviews the expected JSON for each before the parser is written.

**Choice:** Option 2.

**Reasoning:** Removes a whole build-and-validate-a-generator step from
Phase 1 without weakening the test-first rule — fixtures are still a
(statement, expected JSON) pair, and the parser still isn't written until
the fixture exists. Traded off: no longer get a reusable generator as a
byproduct, so if more statements are needed later (more personas, edge
cases) they'll need to be supplied the same way or the generator work
picked up separately.

## 2026-08-09 — Demo mode: allow visitor-uploaded synthetic statements

**Problem:** Original demo mode design (`PROJECT_BRIEF.md`) only supports
picking from 5 pre-computed personas, read as static JSON with no backend
call. The owner wants hiring managers to be able to upload their own
synthetic statement and watch the pipeline run on it, for a stronger
portfolio demo.

**Options considered:**
1. Persona-only demo mode (original plan) — fastest, zero cold-start risk,
   but a passive experience.
2. Also support uploading a synthetic statement live, reusing the app's
   real (in-memory, never-persisted) extraction pipeline.

**Choice:** Option 2, as a Phase 6 stretch goal — not built yet.

**Reasoning:** This is not the real-statement-upload question above; the
input is still synthetic, so rule 8 doesn't apply. It does mean the free-tier
cold-start problem `PROJECT_BRIEF.md` calls out has to be solved for this
path too (or the live-upload demo needs its own warm-keeping story) — design
that when Phase 6 starts, not before.
