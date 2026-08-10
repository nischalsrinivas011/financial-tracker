"""Export arjun_salaried's seeded data as static JSON for the frontend's demo mode.

Goes through the real /accounts, /transactions, /transactions/summary endpoints
via TestClient (same technique as seed_persona.py) so the exported shape is
byte-for-byte what those endpoints actually return - no parallel serialization
to drift out of sync. Demo mode renders this file directly, with no backend
call, so a recruiter's first click doesn't hit Render's free-tier cold start.

Run after seed_persona.py has populated the eval persona's data.
"""

import json
from pathlib import Path

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

from fastapi.testclient import TestClient

import app.api.deps as deps
from app.main import app
from eval.seed_persona import EVAL_CLERK_USER_ID

OUT_PATH = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "demo-data.json"

# A hand-picked, diverse subset of golden_questions.yaml, with answers taken
# verbatim from eval/results/2026-08-10_baseline.json - the actual hybrid
# answer assembly output, not hand-written copy.
DEMO_QA = [
    {
        "question": "How much did I spend on food delivery in March?",
        "answer": "You spent ₹3,064.00 on food delivery in March, across 5 transactions.",
        "route": "sql",
    },
    {
        "question": "What was my largest single transaction last quarter?",
        "answer": "Your largest transaction in the last quarter (Jan-Mar 2026) was ₹38,000.00 to PRAKASH REDDY on 2026-01-03.",
        "route": "sql",
    },
    {
        "question": "Should I prepay my home loan or invest the surplus?",
        "answer": (
            "To help you decide whether to prepay your home loan or invest the surplus, "
            "let's consider the context provided [prepay-vs-invest]. \n\n"
            "Prepaying your home loan offers a **guaranteed, risk-free return equal to the "
            "loan's interest rate**, saving you that much interest every time you prepay. "
            "On the other hand, investing the surplus in equity offers a **higher expected "
            "return over the long run, but it isn't guaranteed**. \n\n"
            "If your loan's interest rate is high (e.g., unsecured personal loans, most "
            "credit card debt), prepayment tends to win because the guaranteed saving is "
            "hard to beat. However, if your loan's rate is low (e.g., some subsidised or "
            "long-tenure secured loans) and you have a long investment horizon and the risk "
            "tolerance for it, investing the surplus can plausibly come out ahead.\n\n"
            "Consider your loan's interest rate and your overall financial situation before "
            "making a decision."
        ),
        "route": "hybrid",
    },
]


def export_demo_data():
    app.dependency_overrides[deps.require_clerk_user_id] = lambda: EVAL_CLERK_USER_ID
    client = TestClient(app)
    headers = {"Authorization": "Bearer eval-seed"}

    try:
        accounts = client.get("/accounts", headers=headers)
        accounts.raise_for_status()
        transactions = client.get("/transactions", headers=headers, params={"limit": 1000})
        transactions.raise_for_status()
        summary = client.get("/transactions/summary", headers=headers)
        summary.raise_for_status()
    finally:
        app.dependency_overrides.clear()

    payload = {
        "accounts": accounts.json(),
        "transactions": transactions.json(),
        "summary": summary.json(),
        "qa": DEMO_QA,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(payload['accounts'])} accounts, {len(payload['transactions'])} transactions)")


if __name__ == "__main__":
    export_demo_data()
