# Decisions log

Real design decisions with alternatives, logged as they're made. See
`CLAUDE.md` for the rules these decisions produced, and `PROJECT_BRIEF.md`
for the roadmap they slot into.

## 2026-08-09 — Categorisation cascade: build deterministic stages first, defer the LLM stage

**Problem:** Phase 2 is scoped as a 3-stage cascade (rules → lookup table →
LLM for the unseen tail). Surveying all 5 personas' fixtures found 91
distinct bank merchants and 43 card descriptions, all resolvable by
structural narration rules or a merchant lookup table — zero genuinely
unseen merchants in the current data.

**Options considered:**
1. Build all 3 stages now, including a stub/mocked LLM call for the unseen
   tail, so the architecture is "complete" per the roadmap description.
2. Build stages 1-2 (rules, lookup table) now, fully tested against fixture
   ground truth; defer stage 3 until there's a real unseen-merchant case to
   test it against and the provider/API key question is settled.

**Choice:** Option 2.

**Reasoning:** Same principle already applied to the card statement parser's
page-overflow handling: don't write code that can't be verified against a
real fixture. A stubbed LLM call would be untested by construction. Stage 3
also needs a decision only the owner can make (which free-tier provider,
and obtaining the API key) and `CLAUDE.md`'s LLM provider rules (cost
routing, token/latency logging, no provider SDK outside
`app/llm/client.py`) are enough scope to deserve their own explained step
rather than being folded in as a side effect of finishing the cascade.
Revisit when either real data introduces an unseen merchant, or there's a
deliberate reason to build and test the LLM stage against a manufactured
case.

## 2026-08-09 — LLM client: one HTTP client for the providers, provider order, deferred UI picker

**Problem:** Building the LLM stage of the categorisation cascade across
free-tier providers with automatic fallback when one is rate-limited. The
owner also asked for the *end user* of the app to eventually be able to
pick their preferred provider, the way a person picks a model in a chat UI.

**Options considered (client shape):**
1. Integrate each provider's official SDK (`google-generativeai`, `groq`,
   `mistralai`, etc.) behind a common interface.
2. One generic HTTP client (`httpx`) against each provider's
   OpenAI-compatible chat-completions endpoint, since each one exposes one.

**Choice:** Option 2. The request/response shapes are close enough to
identical across providers that maintaining a separate SDK adapter per
provider would be pure overhead; one `POST .../chat/completions` call
handles all of them, and it keeps `app/llm/client.py` as the only place
any provider-specific detail (base URL, model, env var) lives, per the
existing "no provider SDK outside this module" rule.

**Provider order:** Groq, Gemini, Mistral - verified against each
provider's own site/docs in August 2026 rather than assumed. Groq does
not train on free-tier inputs; Gemini and Mistral do, by default (Mistral
has an opt-out, not on by default). Cerebras was evaluated during design
(also doesn't train on inputs, per its own site — a general platform
statement, not explicitly scoped to the free tier) and would have been
tried alongside Groq first, but the owner was unable to obtain an API key
for it, so it's not in the final list. That's an access constraint, not a
privacy or quality judgment against Cerebras — worth revisiting if a key
becomes available later.

**Options considered (per-user provider selection):**
1. Build a selector now, as part of finishing the cascade's third stage.
2. Build the supporting data model now (each `Provider` carries
   `trains_on_free_tier_inputs` and a `privacy_note`, and `complete()`
   takes an optional `preferred_provider` override) but not the actual
   picker UI.

**Choice:** Option 2. There is no UI in this project yet - no API
(Phase 3), no frontend (Phase 6) - so there is nothing to select *in*.
Building a selector now would be scaffolding ahead of the current phase,
which the working-style rules explicitly warn against. The data a picker
would need (per-provider training-on-inputs status, an override hook) is
cheap to design in now and expensive to retrofit later, so that part is
built; the control itself is deferred to whichever phase first has a UI.

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

## 2026-08-09 — Knowledge corpus: drop tax content, keep the hybrid architecture

**Problem:** `PROJECT_BRIEF.md` and `CLAUDE.md` originally scoped the
advisory layer's knowledge corpus around Indian tax topics (80C/80D, HRA,
LTCG, PPF/NPS taxation, old-vs-new regime). The owner corrected this
mid-Phase-4: the product is a financial expense tracker and insight
generator, not a tax tool - tax content doesn't belong in it at all.

**Options considered:**
1. Drop the knowledge corpus and hybrid retrieval entirely; pivot to a
   pure SQL/analytics insight generator over transactions.
2. Keep the SQL + vector hybrid architecture (still the portfolio's core
   retrieval-judgment demonstration), but rescope the corpus to general
   personal-finance topics with no tax content, and rewrite the
   tax-rooted questions in `golden_questions.yaml` to match.

**Choice:** Option 2.

**Reasoning:** The retrieval-architecture demonstration (SQL for a
user's actual numbers + vector search for a knowledge framework +
router deciding which is needed) doesn't depend on the corpus topic
being tax specifically - emergency funds, debt ratios, affordability,
and credit mechanics exercise the same architecture just as well, and
are more evergreen than tax figures that shift with each Union Budget.
Of the 27 originally-scoped chunk ids, 14 were tax-specific and dropped
(80c-overview, regime-comparison, 80d-parents, 80d-limits, ltcg-equity,
holding-periods, slabs-new, slabs-old, hra-rules, hra-plus-homeloan,
section-24b, ppf-taxation, nps-80ccd, 80c-eligible-instruments), plus
elss-basics (its defining feature is its tax treatment, so it isn't a
coherent topic without one). 12 non-tax chunks were already in scope
and are kept. 9 new non-tax chunks replace what was dropped:
budgeting-50-30-20, term-insurance-coverage, asset-allocation-by-age,
parking-short-term-funds, rent-vs-buy, sip-mechanics,
credit-utilization-ratio, debt-payoff-strategies, healthy-debt-to-income.

`golden_questions.yaml`'s own header says never soften existing
questions, only add - but 8 of 10 `vec-*` questions and 2 of 8 `hyb-*`
questions were tax-rooted and unanswerable without tax content, so
they're replaced with non-tax equivalents at the same difficulty and
route, not softened or deleted outright. `vec-007`, `vec-008`, and all
of `hyb-001`, `004`-`008` were never tax questions and are untouched.

## 2026-08-09 — Embedding model: all-MiniLM-L6-v2 over newer, heavier options

**Problem:** Phase 4 needs a local (never-paid-API, per `CLAUDE.md`'s
stack rule) sentence-transformers model to embed the knowledge corpus
and incoming queries.

**Options considered:**
1. A newer, higher-retrieval-quality model (BGE-M3, Nomic Embed v2) -
   current research/benchmark writeups rank these above the older
   Sentence-BERT models on pure retrieval quality.
2. `all-MiniLM-L6-v2` - smaller, older, "outperformed by newer models"
   per the same sources, but ~80MB and no special loading requirements.

**Choice:** Option 2.

**Reasoning:** This has to run inside the same process as the deployed
API on Render's free tier - CPU-only, limited RAM. Some Nomic variants
need `trust_remote_code=True` to load, which means running
model-repo-supplied code; that's a deliberate call to make on purpose,
not a default to accept for a marginal quality gain. BGE-M3 is
described in the sources checked as GPU-oriented. For a 21-chunk
corpus, the retrieval-quality gap between MiniLM and a heavier model
is unlikely to be what makes or breaks the Phase 5 eval numbers, and
"picked the lighter model given free-tier deploy constraints" is a
more honest engineering story for the portfolio than chasing benchmark
scores at the cost of what can actually run in production. Revisit if
Phase 5's eval shows retrieval quality is the binding constraint, not
routing or prompting.

## 2026-08-09 — Router: rule-based first, measured at 94.4% against the golden set

**Problem:** `RAG_EVALUATION.md` names routing accuracy as the single
most important metric (target >95%, "cheapest to get right, most
damaging to get wrong"). Needed a first implementation to measure
against the real 36-question golden set, not just design in the
abstract.

**Options considered:**
1. LLM-based classification for every question.
2. Rule-based keyword classifier first (same precedent as the
   categorisation cascade: rules before LLM), falling back to an LLM
   router only if rules can't clear a reasonable bar.

**Choice:** Option 2, built and measured.

**Result:** 34/36 (94.4%) against the full golden set - just under the
95% target. Both misses are `edge-003` ("Am I spending too much?") and
`edge-005` ("Summarise my finances.") - the file's own "edge cases -
where products actually break" section. Both confidently match an
SQL-only signal (personal-data reference) and no corpus-signal
keyword, so they land on `sql` instead of `hybrid`.

**Reasoning for not chasing the last 2 questions with more keywords:**
hand-crafting patterns for these two exact phrases would be tuning to
memorize the eval set, not building a router that generalizes to
questions not in it - the same concern `golden_questions.yaml`'s own
header raises about not editing questions to match model behaviour,
applied to the router instead of the corpus. This is documented as a
known, understood limitation (`tests/test_rag_router.py`'s
`KNOWN_MISSES`) rather than silently accepted or hidden behind a
loosened assertion.

**Not yet decided:** whether closing the gap to >95% is worth an
LLM-based fallback for low-confidence cases (mirroring the
categorisation cascade's stage 3) before Phase 5's formal baseline
run, or whether 94.4% with two well-understood, documented misses is
an acceptable baseline to carry into Phase 5 and revisit there with
real eval infrastructure. Owner's call, not made yet.

## 2026-08-10 — Groundedness calibration: 6-question subset, and why Claude can't do the labeling

**Problem:** `RAG_EVALUATION.md` requires calibrating the groundedness
judge by hand-labeling answers independently and reporting judge-human
agreement. The full judged set is 18 questions / 147 claims - too much
for the owner to get through in one sitting. Separately, the owner asked
whether Claude could do the hand-labeling instead.

**On Claude doing the labeling:** declined, not deferred. Calibration
exists to answer "does the judge - an LLM - agree with independent human
judgment?" If the same kind of model (or Claude specifically) generates
both the judge's verdicts and the "human" comparison labels, the
resulting agreement number is one LLM checking another wearing a
different hat, not a real calibration signal. Reporting that as human
calibration in the portfolio would misrepresent what was actually
measured.

**Options considered for making the real labeling tractable:**
1. Keep all 18 questions / 147 claims.
2. Reduce to a smaller representative subset.
3. Coarser per-question (not per-claim) labels across all 18.
4. Defer calibration entirely, document as an unresolved gap.

**Choice:** Option 2. Subset: `vec-001, vec-002, vec-005, hyb-001,
hyb-006, hyb-007` - 3 vector + 3 hybrid, spanning easy/medium/hard
difficulty and distinct topics (budgeting, insurance, housing,
prepay-vs-invest, savings, affordability). 48 claims, not 147.

**Reasoning:** A real, honest sample the owner can actually complete
beats either a token few claims or an abandoned calibration. Per-claim
(not per-question) granularity kept for this subset, since that's what
the groundedness metric itself measures (RAG_EVALUATION.md section 3:
"percentage of claims traceable to a source") - a coarser per-question
label would measure something adjacent, not the same thing the judge
computes, making the agreement figure less directly comparable.
`eval/CALIBRATION.md` now states explicitly it's 6 of 18, not silently
presented as the full set.
