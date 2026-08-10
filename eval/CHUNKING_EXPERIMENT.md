# Chunking experiment

Raw data: `eval/results/2026-08-10_chunking-experiment.json`. Methodology
and code: `eval/chunking_strategies.py`, `eval/run_chunking_experiment.py`.

## Hypothesis (stated before running, per RAG_EVALUATION.md)

> Personal-finance frameworks are highly structured, so section-aware
> should beat fixed-size on recall because a rule of thumb and its
> caveats/conditions live in the same section and fixed-size splits them
> apart.

**The hypothesis did not hold** — fixed-size scored higher recall@5
(100.0%) than section-aware (88.0%).

## Results

| Strategy | Chunks | P@5 | R@5 | MRR |
|---|---|---|---|---|
| Section-aware | 21 | 26.7% | 88.0% | 0.96 |
| Fixed-size (512 tok, 50 overlap) | 11 | 30.0% | 100.0% | 0.85 |
| Semantic (percentile boundary) | 35 | 38.9% | 81.5% | 0.83 |

## Why the hypothesis didn't hold — a corpus-size confound, not a wrong hypothesis

Fixed-size chunking produced only 11 chunks from the same source text
(vs. 21 section-aware, 35 semantic) because each 512-token window is wide
enough to span multiple original sections — confirmed directly while
building this: one fixed-size chunk's provenance was
`{cc-revolving-interest, credit-utilization-ratio, credit-score-factors,
cc-late-payment}`, all four `credit_cards.md` sections in one window.

That's exactly the failure mode the hypothesis predicted. But it has a
side effect the hypothesis didn't account for: **retrieving k=5 out of
only 11 total chunks samples ~45% of the entire corpus**, versus k=5 out
of 21 section-aware chunks sampling ~24%. With windows this wide, a
relevant section is very likely to be *somewhere* inside the 5 retrieved
chunks almost by construction — not because fixed-size chunking found the
right content more precisely, but because there's much less corpus left
*not* being retrieved. Recall@k isn't comparable across strategies with
very different total chunk counts without accounting for this.

**MRR tells a more informative story than recall@5 here.** Section-aware
has the best MRR (0.96) — when it retrieves a relevant chunk, that chunk
is almost always ranked first. Fixed-size's MRR (0.85) is worse despite
its higher recall: it finds *a* relevant chunk within the top 5 more
often, but that chunk is less reliably the top-ranked result, consistent
with wider windows diluting a chunk's specific topical relevance with
neighboring, less-relevant content.

Semantic chunking (35 chunks, the most fine-grained) has the *highest*
precision@5 (38.9%) but the *lowest* recall@5 (81.5%) and MRR (0.83) — the
percentile-based boundary threshold fragmented some sections quite finely
(the `budgeting-50-30-20` section alone split into 5 chunks in manual
inspection), and very small chunks can each be individually precise but
collectively miss covering a full concept, and rank less reliably at the
top since no single small fragment captures a section's full context.

## What this means for the production strategy

Phase 4 already put section-aware into production
(`app/rag/chunking.py`), and this result doesn't change that call: MRR is
the more relevant metric for a system that synthesizes an answer from a
handful of top-ranked chunks (this project's actual retrieval pattern,
`app/rag/retrieval.py`'s `search(k=5)` feeding `app/rag/answer.py`), and
section-aware wins on MRR. Fixed-size's recall advantage is a corpus-size
artifact of this specific 21-vs-11-chunk comparison, not evidence it
retrieves more precisely.

**Not done, and worth being honest about as a limitation of this
experiment**: recall@k should really be evaluated at a k proportional to
corpus size (or precision/recall reported as full curves) to remove the
chunk-count confound cleanly. Not built in this pass — logged here rather
than silently accepted as a clean win for section-aware, since the raw
recall numbers alone would suggest the opposite conclusion.
