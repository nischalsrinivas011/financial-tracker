"""Chunk knowledge/*.md, embed each chunk, and upsert into knowledge_chunks.

Idempotent: re-running after editing a corpus file updates the existing
row for that chunk_id (matched via ON CONFLICT) rather than duplicating it.
"""

from pathlib import Path

if __name__ == "__main__":
    # Must run before importing app.db.session below, which reads
    # DATABASE_URL eagerly at import time - load_dotenv() in the __main__
    # block at the bottom of this file would run too late to help.
    from dotenv import load_dotenv

    load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk
from app.db.session import SessionLocal
from app.rag.chunking import load_corpus_chunks
from app.rag.embeddings import embed_batch

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"


def ingest_corpus(knowledge_dir: Path = KNOWLEDGE_DIR, db: Session | None = None) -> int:
    chunks = load_corpus_chunks(knowledge_dir)
    embeddings = embed_batch([c.content for c in chunks])

    owns_session = db is None
    session = db or SessionLocal()
    try:
        for chunk, embedding in zip(chunks, embeddings):
            stmt = pg_insert(KnowledgeChunk).values(
                chunk_id=chunk.chunk_id, source_file=chunk.source_file,
                heading=chunk.heading, content=chunk.content, embedding=embedding,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["chunk_id"],
                set_=dict(
                    source_file=stmt.excluded.source_file, heading=stmt.excluded.heading,
                    content=stmt.excluded.content, embedding=stmt.excluded.embedding,
                ),
            )
            session.execute(stmt)
        session.commit()
    finally:
        if owns_session:
            session.close()
    return len(chunks)


if __name__ == "__main__":
    n = ingest_corpus()
    print(f"ingested {n} chunks")
