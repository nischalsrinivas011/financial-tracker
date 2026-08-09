"""Section-aware chunking of the knowledge/*.md corpus (the one strategy
Phase 4 builds; fixed-size and semantic chunking are Phase 5's comparison,
see RAG_EVALUATION.md).

Splits on `## Heading <!-- chunk_id: some-id -->` markers rather than on
generic markdown heading levels, so the mapping from section to chunk_id
(the id golden_questions.yaml's relevant_chunks refers to) is explicit
and doesn't depend on guessing a slug from heading text.
"""

import re
from dataclasses import dataclass
from pathlib import Path

_HEADING_RE = re.compile(
    r"^## (?P<heading>.+?) <!-- chunk_id: (?P<chunk_id>[\w-]+) -->\s*$",
    re.MULTILINE,
)


@dataclass
class Chunk:
    chunk_id: str
    heading: str
    content: str
    source_file: str


def parse_markdown_chunks(text: str, source_file: str) -> list[Chunk]:
    matches = list(_HEADING_RE.finditer(text))
    chunks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        chunks.append(Chunk(
            chunk_id=m.group("chunk_id"),
            heading=m.group("heading"),
            content=content,
            source_file=source_file,
        ))
    return chunks


def load_corpus_chunks(knowledge_dir: Path) -> list[Chunk]:
    chunks = []
    for md_file in sorted(knowledge_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        chunks.extend(parse_markdown_chunks(text, source_file=md_file.name))
    return chunks
