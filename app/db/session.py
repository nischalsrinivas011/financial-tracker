"""Engine and session factory for the Postgres (Neon) connection.

DATABASE_URL is read eagerly at import time. There is no local-database
fallback by design (project decision: tests run against the real Neon
instance, not SQLite), so a missing DATABASE_URL is a hard failure here
rather than something to silently work around.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _engine_url() -> str:
    url = os.environ["DATABASE_URL"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(_engine_url())
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
