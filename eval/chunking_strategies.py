"""Fixed-size and semantic chunking, for the Phase 5 comparison experiment
(RAG_EVALUATION.md) against the section-aware strategy Phase 4 already
built and put into production (app/rag/chunking.py). Not used by the app -
Phase 4 already chose section-aware as the live strategy; this lives in
eval/ on purpose, kept separate.

Provenance tracking: golden_questions.yaml's relevant_chunks ground truth
is defined in terms of the original section-aware chunk ids. A fixed-size
or semantic chunk here doesn't line up 1:1 with those sections, so each
experimental chunk records which original chunk_id(s) its word range
overlaps - a retrieved chunk counts as a match for a ground-truth id if
that id is in its provenance set, not by exact chunk_id equality.

Windows are computed per source file, not across file boundaries - each
knowledge/*.md file is a genuinely separate source document (different
topic area), the same way separate documents in a real corpus wouldn't
get merged into one window.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.rag.chunking import _HEADING_RE

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class ExperimentChunk:
    content: str
    provenance: set[str] = field(default_factory=set)


def _sections_with_word_offsets(text: str) -> list[dict]:
    """Like app.rag.chunking.parse_markdown_chunks, but also returns each
    section's word-index range in the concatenated body - the provenance
    bookkeeping fixed-size/semantic chunking needs.
    """
    matches = list(_HEADING_RE.finditer(text))
    sections = []
    cumulative = 0
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        words = text[start:end].strip().split()
        sections.append({
            "chunk_id": m.group("chunk_id"),
            "words": words,
            "word_start": cumulative,
            "word_end": cumulative + len(words),
        })
        cumulative += len(words)
    return sections


def _load_file_sections(knowledge_dir: Path) -> list[list[dict]]:
    return [_sections_with_word_offsets(md.read_text(encoding="utf-8")) for md in sorted(knowledge_dir.glob("*.md"))]


def fixed_size_chunks(knowledge_dir: Path, window: int = 512, overlap: int = 50) -> list[ExperimentChunk]:
    chunks = []
    for sections in _load_file_sections(knowledge_dir):
        all_words = [w for s in sections for w in s["words"]]
        step = window - overlap
        i = 0
        while i < len(all_words):
            window_words = all_words[i:i + window]
            word_start, word_end = i, i + len(window_words)
            provenance = {
                s["chunk_id"] for s in sections
                if s["word_start"] < word_end and s["word_end"] > word_start
            }
            chunks.append(ExperimentChunk(content=" ".join(window_words), provenance=provenance))
            if word_end >= len(all_words):
                break
            i += step
    return chunks


def _sentences_with_chunk_id(sections: list[dict]) -> list[dict]:
    result = []
    for s in sections:
        text = " ".join(s["words"])
        for sent in _SENTENCE_RE.split(text):
            sent = sent.strip()
            if sent:
                result.append({"text": sent, "chunk_id": s["chunk_id"]})
    return result


def _cosine(a, b) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def semantic_chunks(knowledge_dir: Path, boundary_percentile: float = 0.25) -> list[ExperimentChunk]:
    from app.rag.embeddings import embed_batch

    per_file_sentences = [_sentences_with_chunk_id(sections) for sections in _load_file_sections(knowledge_dir)]

    # Threshold calibrated from the actual corpus, not a guessed constant:
    # the boundary_percentile-th percentile of all observed adjacent-sentence
    # similarities, corpus-wide.
    all_sims = []
    per_file_embeddings = []
    for sentences in per_file_sentences:
        embeddings = embed_batch([s["text"] for s in sentences]) if sentences else []
        per_file_embeddings.append(embeddings)
        all_sims.extend(_cosine(embeddings[i], embeddings[i + 1]) for i in range(len(embeddings) - 1))

    all_sims.sort()
    threshold = all_sims[int(len(all_sims) * boundary_percentile)] if all_sims else 0.0

    chunks = []
    for sentences, embeddings in zip(per_file_sentences, per_file_embeddings):
        if not sentences:
            continue
        boundaries = [0]
        for i in range(1, len(sentences)):
            if _cosine(embeddings[i - 1], embeddings[i]) < threshold:
                boundaries.append(i)
        boundaries.append(len(sentences))

        for start, end in zip(boundaries, boundaries[1:]):
            group = sentences[start:end]
            content = " ".join(s["text"] for s in group)
            provenance = {s["chunk_id"] for s in group}
            chunks.append(ExperimentChunk(content=content, provenance=provenance))

    return chunks


def section_aware_chunks(knowledge_dir: Path) -> list[ExperimentChunk]:
    """The production strategy (app/rag/chunking.py), wrapped with a
    trivial provenance set for a consistent interface with the other two.
    """
    from app.rag.chunking import load_corpus_chunks

    return [ExperimentChunk(content=c.content, provenance={c.chunk_id}) for c in load_corpus_chunks(knowledge_dir)]
