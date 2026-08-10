"""Seed a real eval user with arjun_salaried's fixture statements.

Goes through the actual /statements/bank and /statements/card endpoints
via TestClient - not duplicated upload logic - with only the Clerk auth
dependency overridden to a fixed known user. golden_questions.yaml's
meta.persona is "salaried_bengaluru_v1": arjun_salaried is the HDFC Bank,
Bengaluru-based salaried persona (see PROJECT_BRIEF.md's persona list).

Idempotent: re-running just re-uploads into the same account, and the
upload endpoint's own ON CONFLICT DO NOTHING dedupes the transactions.
"""

from pathlib import Path

if __name__ == "__main__":
    # Must run before importing app.main below, which imports
    # app.db.session, which reads DATABASE_URL eagerly at import time.
    from dotenv import load_dotenv

    load_dotenv()

from fastapi.testclient import TestClient

import app.api.deps as deps
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app

EVAL_CLERK_USER_ID = "eval_persona_salaried_bengaluru_v1"
FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "arjun_salaried"


def seed_persona():
    app.dependency_overrides[deps.require_clerk_user_id] = lambda: EVAL_CLERK_USER_ID
    client = TestClient(app)

    try:
        for endpoint, filename in [
            ("/statements/bank", "arjun_salaried_FY2025-26_bank.pdf"),
            ("/statements/card", "arjun_salaried_FY2025-26_card.pdf"),
        ]:
            path = FIXTURES / filename
            with open(path, "rb") as f:
                response = client.post(
                    endpoint,
                    files={"file": (filename, f, "application/pdf")},
                    headers={"Authorization": "Bearer eval-seed"},
                )
            response.raise_for_status()
            print(endpoint, response.json())
    finally:
        app.dependency_overrides.clear()

    db = SessionLocal()
    try:
        user = db.query(User).filter_by(clerk_user_id=EVAL_CLERK_USER_ID).one()
        return user.id
    finally:
        db.close()


if __name__ == "__main__":
    user_id = seed_persona()
    print("eval persona user_id:", user_id)
