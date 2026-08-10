from pathlib import Path

import yaml

from app.rag.chunking import load_corpus_chunks, parse_markdown_chunks

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


def _required_chunk_ids() -> set[str]:
    with open(Path(__file__).parent.parent / "eval" / "golden_questions.yaml") as f:
        data = yaml.safe_load(f)
    required = set()
    for q in data["questions"]:
        required.update(q.get("relevant_chunks", []) or [])
    return required


def test_parses_a_single_heading():
    text = "# Title\n\n## A Heading <!-- chunk_id: my-id -->\n\nSome content.\nMore content.\n"
    chunks = parse_markdown_chunks(text, source_file="x.md")

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "my-id"
    assert chunks[0].heading == "A Heading"
    assert chunks[0].content == "Some content.\nMore content."


def test_parses_multiple_headings_in_one_file():
    text = (
        "# Title\n\n"
        "## First <!-- chunk_id: first-id -->\n\nfirst content\n\n"
        "## Second <!-- chunk_id: second-id -->\n\nsecond content\n"
    )
    chunks = parse_markdown_chunks(text, source_file="x.md")

    assert [c.chunk_id for c in chunks] == ["first-id", "second-id"]
    assert chunks[0].content == "first content"
    assert chunks[1].content == "second content"


def test_corpus_matches_golden_questions_exactly():
    chunks = load_corpus_chunks(KNOWLEDGE_DIR)
    found_ids = [c.chunk_id for c in chunks]

    assert len(found_ids) == len(set(found_ids)), "duplicate chunk_id found"
    assert set(found_ids) == _required_chunk_ids()


def test_every_chunk_has_nonempty_content():
    chunks = load_corpus_chunks(KNOWLEDGE_DIR)
    for c in chunks:
        assert len(c.content) > 50, f"{c.chunk_id} has suspiciously little content"
