"""Ingestion runs against real Neon via the injected db_session fixture
(rollback-per-test, same pattern as the rest of the DB tests), not the
real knowledge_chunks table - keeps this from polluting or depending on
whatever's actually been ingested for real.
"""

from app.db.models import KnowledgeChunk
from app.rag.ingest import KNOWLEDGE_DIR, ingest_corpus


def test_ingest_populates_all_21_chunks_with_embeddings(db_session):
    count = ingest_corpus(KNOWLEDGE_DIR, db=db_session)
    db_session.flush()

    assert count == 21
    stored = db_session.query(KnowledgeChunk).all()
    assert len(stored) == 21

    sample = db_session.query(KnowledgeChunk).filter_by(chunk_id="budgeting-50-30-20").one()
    assert "50%" in sample.content
    assert len(sample.embedding) == 384


def test_ingest_is_idempotent_on_rerun(db_session):
    ingest_corpus(KNOWLEDGE_DIR, db=db_session)
    db_session.flush()
    ingest_corpus(KNOWLEDGE_DIR, db=db_session)  # must update, not duplicate
    db_session.flush()

    count = db_session.query(KnowledgeChunk).count()
    assert count == 21
