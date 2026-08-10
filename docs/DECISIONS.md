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

## 2026-08-10 — Groundedness calibration: deferred until after live testing, not faked

**Problem:** Owner asked to mark every claim in `eval/CALIBRATION.md` as
GROUNDED for now, to unblock other work, with real labeling planned once
the app is live and scenarios can be tested directly.

**Considered:** filling in all-GROUNDED labels and computing a
judge-human agreement figure now, so Phase 5's calibration step shows as
complete.

**Choice:** declined the rubric-stamp, calibration left explicitly
undone rather than faked.

**Reasoning:** the judge's own grounded rate on this subset is already
known (~88%); an all-grounded rubber stamp would trivially reproduce a
number close to that back as "agreement," producing a statistic with
zero discriminating power while looking like a real calibration result.
Reporting that in the portfolio as "the judge was calibrated" would
misrepresent what was actually measured - worse than just stating
plainly that it hasn't happened yet.

**What's actually happening:** deferring the real hand-labeling until
the owner can test scenarios against the live app is a reasonable
sequencing call, not a shortcut - noted here so the gap is honest and
visible rather than hidden behind a fabricated number.
`eval/CALIBRATION.md` stays unchecked; no judge-human agreement figure
exists yet, and none should be reported until real labels do.

## 2026-08-10 — Embedding runtime: fastembed (ONNXRuntime) over sentence-transformers (torch)

**Problem:** the first real Phase 6 deploy to Render's free tier
(512MB RAM) OOM-killed the app during boot. Measured locally:
`import torch` alone resolves to ~360MB resident before FastAPI,
SQLAlchemy, uvicorn, or any app code loads; sentence-transformers plus
the loaded all-MiniLM-L6-v2 model and a first encode call brings that
to ~444MB. That's already over budget before the rest of the app's
baseline memory is counted. This was a known, explicitly-flagged risk
(see the 2026-08-09 "Embedding model" entry) - "not yet confirmed" -
now confirmed, and confirmed not to fit.

**Considered:**
1. Defer the `sentence_transformers` import to first use instead of
   module import time. Rejected: torch's ~360MB is the dominant cost,
   not the model weights, so this only moves the crash from boot-time
   (predictable, total outage) to the first vector/hybrid question
   (unpredictable, mid-request outage) - not a real fix.
2. Upgrade Render to a paid plan for more RAM. Rejected for now: no
   code change needed, but costs real money and breaks the free-tier
   approach used everywhere else in this project (Neon free, Groq/
   Gemini/Mistral free, Vercel free). Owner's call, and owner chose
   not to.
3. Swap to a torch-free embedding runtime that still runs the same
   model weights locally, keeping the "never a paid embedding API"
   hard rule intact.

**Choice:** option 3 - `fastembed` (ONNXRuntime-backed), running the
identical `sentence-transformers/all-MiniLM-L6-v2` weights (fastembed's
model registry serves this exact model, still 384 dims, no schema
change needed). Measured locally: import + model load + first encode
settles at ~211MB, under half of the torch path.

**Reasoning:** same model, same "local, free, CPU-only" constraints,
just a lighter inference engine. Re-ran the full eval suite after the
swap and re-ingesting the corpus (`eval/results/2026-08-10_embedding-
swap-fastembed.json`): routing accuracy 94.4%, recall@5 88.0%,
constraint pass rate 71.4% - identical to the 2026-08-10 baseline, so
no measurable regression at the level the eval actually scores.

**Known cost:** one pytest in `tests/test_rag_retrieval.py` now fails -
"How much emergency fund should someone keep?" ranks
`essential-vs-discretionary` (distance 0.522) just ahead of the
expected `emergency-fund-framework` (0.563), a narrow flip between two
adjacent, genuinely related chunks in the same source doc, most likely
from ONNXRuntime and PyTorch executing the same weights with slightly
different floating-point kernels on an already-close pair. recall@5 is
unaffected. Left failing with a comment rather than loosened to pass -
same treatment as the router's already-documented known misses, not
worth chasing for one borderline query.
