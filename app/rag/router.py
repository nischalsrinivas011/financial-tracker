"""Route a question to sql / vector / hybrid / refuse.

Deterministic and keyword-based on purpose (same "rules before LLM"
precedent as app/categorize/cascade.py). The sql/vector decision isn't
one classification - it decomposes into two independent signals: does
the question need the user's actual transaction data, and does it invoke
a general financial framework from the corpus? Both -> hybrid. One only
-> sql or vector. Neither, or a refusal trigger -> refuse.

Refusal patterns are checked first: several (e.g. ref-005 "What's my
credit score?") would otherwise also match the sql/corpus signal
patterns and get misrouted to hybrid instead of refused.
"""

import re
from dataclasses import dataclass

Route = str  # "sql" | "vector" | "hybrid" | "refuse"

_REFUSE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bignore your instructions\b",
        r"\bsystem prompt\b",
        r"\bwhich mutual fund\b",
        r"\bwhich stock\b",
        r"\bwill\b.*\bgo up\b",
        r"\bnifty\b",
        r"\bquit my job\b",
        r"\bavoid paying tax\b",
        r"\bwhat(?:'s| is) my credit score\b",
    ]
]

_SQL_SIGNAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bdid i spend\b",
        r"\bi spend\b",
        r"\bmy spend\b",
        r"\bmy spending\b",
        r"\bmy (largest|biggest) (single )?transaction\b",
        r"\bmy average monthly spend\b",
        r"\bmerchant did i pay\b",
        r"\bpercentage of my income\b",
        r"\bmy income\b",
        r"\bmy emergency fund\b",
        r"\bmy budget\b",
        r"\bmy real numbers\b",
        r"\bmy credit card interest\b",
        r"\bam i (actually )?saving\b",
        r"\bcan i afford\b",
        r"\bmy biggest financial risk\b",
        r"\bmy balance\b",
        r"\bmy finances\b",
        r"\bmy home loan\b",
        r"\bdebt each month\b",
        r"\bspending too much\b",
        r"\bspend at that place\b",
    ]
]

_CORPUS_SIGNAL_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b50/30/20\b",
        r"\bbudgeting rule\b",
        r"\blife insurance\b",
        r"\binsurance coverage\b",
        r"\bequity/debt mix\b",
        r"\bpark money\b",
        r"\brent or buy\b",
        r"\bsip\b",
        r"\bemergency fund\b",
        r"\bmiss a credit card payment\b",
        r"\bcredit utilization\b",
        r"\bcredit score\b",
        r"\bsnowball\b",
        r"\bavalanche\b",
        r"\bprepay\b",
        r"\binvest the surplus\b",
        r"\bgoing toward debt\b",
        r"\bafford\b",
        r"\bhome loan\b",
        r"\bfinancial risk\b",
        r"\bsaving\b",
        r"\bcredit card interest\b",
    ]
]


@dataclass
class RouteResult:
    route: Route
    needs_sql: bool
    needs_corpus: bool
    matched_refuse: bool


def route(question: str) -> RouteResult:
    if any(p.search(question) for p in _REFUSE_PATTERNS):
        return RouteResult(route="refuse", needs_sql=False, needs_corpus=False, matched_refuse=True)

    needs_sql = any(p.search(question) for p in _SQL_SIGNAL_PATTERNS)
    needs_corpus = any(p.search(question) for p in _CORPUS_SIGNAL_PATTERNS)

    if needs_sql and needs_corpus:
        chosen = "hybrid"
    elif needs_sql:
        chosen = "sql"
    elif needs_corpus:
        chosen = "vector"
    else:
        chosen = "refuse"  # no signal matched: safer to decline/hedge than guess

    return RouteResult(route=chosen, needs_sql=needs_sql, needs_corpus=needs_corpus, matched_refuse=False)
