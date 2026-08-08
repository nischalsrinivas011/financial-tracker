# RAG evaluation

The point of this document is to make quality measurable rather than vibes-based.
Everything below is designed so that a change to chunking, retrieval, or prompting
produces a number that moves.

## Repo layout

```
eval/
  golden_questions.yaml      # the frozen question set
  chunk_labels.yaml          # question_id -> relevant chunk ids (ground truth)
  run_eval.py                # entry point
  metrics/
    retrieval.py             # precision@k, recall@k, MRR
    groundedness.py          # LLM-as-judge
    routing.py               # did the router pick sql/vector/hybrid correctly
  judges/
    groundedness_prompt.txt
    refusal_prompt.txt
  results/
    2026-08-09_baseline.json
    2026-08-14_semantic-chunking.json
    ...
  report.py                  # results/*.json -> markdown table
```

Every run writes a timestamped JSON. Never overwrite. The history *is* the artifact.

## What gets measured

### 1. Routing accuracy
Before retrieval quality matters, the router has to pick the right path. For each
question, compare the chosen route against the `route` field.

- **Metric:** accuracy, plus a confusion matrix.
- **Why it matters:** firing vector search on `sql-001` wastes money and adds
  hallucination surface. Firing SQL alone on `hyb-001` gives a numerically correct
  answer with no reasoning behind it.
- **Target:** >95%. This is the cheapest thing to get right and the most damaging
  to get wrong.

### 2. Retrieval precision and recall @k
Only for questions with a non-empty `relevant_chunks`.

- **precision@k** — of the k chunks retrieved, how many were labelled relevant.
- **recall@k** — of the labelled relevant chunks, how many were retrieved.
- **MRR** — how high up the first relevant chunk landed.

Report at k = 3, 5, 10. Recall@5 is the headline number: if the right chunk isn't
in the context, no amount of prompting saves the answer.

### 3. Groundedness
An LLM-as-judge pass. For each generated answer, decompose into atomic claims and
check each against the retrieved context plus the SQL result set.

- **Metric:** percentage of claims traceable to a source. Report the inverse
  (hallucination rate) too — it's the number people actually ask about.
- **Judge model:** use a *different* model than the generator where practical, or at
  minimum a separate call with no access to the generation reasoning.
- **Calibrate the judge.** Hand-label 20 answers yourself, run the judge on the same
  20, report judge-human agreement. An uncalibrated judge is a vibes machine with
  extra steps. Reporting the agreement figure is itself a strong signal.

### 4. Constraint adherence
Mechanical checks against `must_mention` and `must_not_mention`. Cheap, no LLM
needed, catches regressions fast. Run this on every commit.

### 5. Refusal behaviour
For `route: refuse` questions, two failure modes, both worth tracking separately:

- **Under-refusal** — gave specific security recommendations, predicted markets,
  invented a credit score. This is the dangerous one.
- **Over-refusal** — declined something it should have answered. `ref-004` is the
  trap: the model should discuss legal deductions and decline evasion, not refuse
  the whole question.

Over-refusal is the metric most teams forget to track, and mentioning that in an
interview lands well.

### 6. Cost and latency
Per question: input tokens, output tokens, retrieval calls, wall-clock time, total
cost. Aggregate to cost-per-query and p50/p95 latency.

Track this from run one. "I reduced cost per query by 60% by routing simple
lookups away from the LLM" is a portfolio sentence you can only write if you
measured the before.

## The chunking experiment

Run the same golden set against at least three strategies and record the deltas:

| Strategy | Description |
|---|---|
| Fixed-size | 512 tokens, 50-token overlap. The naive baseline. |
| Section-aware | Split on document headings; keep a section intact where possible. |
| Semantic | Embedding-similarity boundaries between adjacent sentences. |

Hypothesis to state *before* running: tax rules are highly structured, so
section-aware should beat fixed-size on recall because a deduction limit and its
conditions live in the same section and fixed-size splits them.

Record whether the hypothesis held. A documented wrong hypothesis is better
portfolio material than an undocumented right one.

## Baseline discipline

Run the full set once, before any tuning, and commit the result as
`baseline.json`. Every subsequent change gets reported as a delta against it.

Change one variable at a time. If you change chunking and the prompt in the same
run, the number tells you nothing.

## Failure log

Keep `eval/FAILURES.md`. Every time a question fails in a way that surprises you,
write a paragraph: what you expected, what happened, what you changed, whether it
worked. Ten honest entries here are worth more to a hiring manager than a green
dashboard, because they show diagnostic ability rather than a lucky configuration.

## What to publish

In the repo README, a single table:

| Metric | Baseline | Current |
|---|---|---|
| Routing accuracy | | |
| Recall@5 | | |
| Groundedness | | |
| Judge-human agreement | | |
| Under-refusal rate | | |
| Over-refusal rate | | |
| Cost per query | | |
| p95 latency | | |

Then link to the failure log and the chunking experiment write-up. That table is
the thing an AI PM hiring manager will actually read.
