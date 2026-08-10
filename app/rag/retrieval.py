"""Vector search over the knowledge corpus.

No vector index (HNSW/IVFFlat) on knowledge_chunks.embedding: at 21 rows a
sequential scan is instant, and an index tuned for a corpus this small
would be premature - revisit if the corpus grows enough for it to matter.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import KnowledgeChunk
from app.rag.embeddings import embed


@dataclass
class RetrievedChunk:
    chunk_id: str
    heading: str
    content: str
    distance: float  # cosine distance: 0 = identical, 2 = opposite. Lower is more similar.


def search(db: Session, query: str, k: int = 5) -> list[RetrievedChunk]:
    query_embedding = embed(query)
    distance = KnowledgeChunk.embedding.cosine_distance(query_embedding)

    rows = (
        db.query(KnowledgeChunk, distance.label("distance"))
        .order_by(distance)
        .limit(k)
        .all()
    )
    return [
        RetrievedChunk(chunk_id=chunk.chunk_id, heading=chunk.heading, content=chunk.content, distance=float(d))
        for chunk, d in rows
    ]
