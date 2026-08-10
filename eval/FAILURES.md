# Failure log

Per RAG_EVALUATION.md: every time a question fails in a way that surprises,
write a paragraph - what was expected, what happened, what changed, whether
it worked. Entries below are from the 2026-08-10 baseline run
(`eval/results/2026-08-10_baseline.json`).

## sql-001, hyb-001, hyb-007 — mechanical constraint checks are too literal (2026-08-10)

**Expected:** `must_mention` failures to mean the answer was missing real
content.

**What happened:** All three answers are substantively correct. sql-001's
answer is `"You spent ₹3,064.00 on food delivery in March, across 5
transactions"` — a clear amount and a clear month — but `must_mention:
[amount, month]` checks for the literal substrings "amount" and "month",
neither of which appears; the answer states a *specific* amount and month
instead of using those generic nouns. hyb-001 and hyb-007 discuss the
underlying trade-off/assumption concepts at length without using the exact
words "trade-off" or "assumption".

**What this means:** `eval/metrics/constraints.py`'s substring check
(`RAG_EVALUATION.md` section 4: "cheap, no LLM needed") is the right tool
for catching a genuinely missing concept, and the wrong tool for checking
whether a concept was *expressed*. Not changed - a naive substring check
producing occasional false negatives on good answers is a known, accepted
limitation of a cheap mechanical check, not a bug to patch by injecting the
literal target words into templates (that would be gaming the metric, not
improving the answer). Groundedness (LLM-as-judge, still pending human
calibration) is the metric that should actually catch whether these
concepts were communicated, not this one.

## hyb-001, hyb-007 — SQL context wasn't actually personal (2026-08-10)

**Expected:** hyb-001 ("Should I prepay my home loan or invest the
surplus?") to pull the user's actual EMI/surplus figures into the SQL
context handed to the LLM.

**What happened:** `answer_sql_question`'s keyword dispatcher doesn't
recognise "prepay"/"surplus"/"home loan" as pointing at any specific
category, so it fell through to the "couldn't identify a category" default
and handed the LLM a clarification message instead of real numbers. The LLM
still produced a reasonable, generically-correct answer from the corpus
alone, which is why this wasn't obviously broken from reading the output -
but it isn't the personalised, grounded-in-your-numbers answer the question
is actually asking for. Same root cause as hyb-007 (FOIR/home-loan
affordability, also no matching category).

**What this means:** confirms the documented scope boundary
(`answer_sql_question` is keyword-matched to the golden set's patterns, not
a general parser) has a real, visible cost for multi-concept questions like
"prepay vs invest" that don't map onto a single known category. Not fixed
now - logged as a known gap (see CLAUDE.md's current-phase notes) rather
than patched with more keywords, same reasoning as the router's known
misses.

## edge-001 — wrong fallback branch, not just an imprecise one (2026-08-10)

**Expected:** "How much did I spend in February?" (no data for that month)
to either report total spend across all categories for February, or state
plainly that there's no data for that period.

**What happened:** the question names no specific category, and
`answer_sql_question`'s default branch requires a category match before it
will compute anything - when `_detect_category` returns None, it
immediately asks "could you name the category or merchant?" instead of
falling back to an all-category total. This is a real logic gap, not a
wording mismatch: category-less date-range questions ("how much did I
spend" with no category) aren't handled at all, so the "no data for this
period" check this edge case was actually designed to test never gets
reached.

**What changed:** nothing yet - documented here and in CLAUDE.md's
current-phase notes as a known gap to fix in a later pass, consistent with
"optimize later" rather than patching mid-Phase-5.
