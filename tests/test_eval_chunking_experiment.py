from eval.chunking_strategies import ExperimentChunk
from eval.run_chunking_experiment import _mrr, _precision_recall_at_k


def test_precision_recall_uses_provenance_not_exact_id():
    # A fixed-size chunk spanning two original sections still counts as a
    # hit for either one - that's the whole point of provenance tracking.
    retrieved = [
        ExperimentChunk(content="a", provenance={"topic-a", "topic-b"}),
        ExperimentChunk(content="c", provenance={"topic-c"}),
    ]
    precision, recall = _precision_recall_at_k(retrieved, {"topic-b"}, k=2)
    assert precision == 0.5  # 1 of 2 retrieved chunks overlaps the target
    assert recall == 1.0  # the only relevant id was found


def test_recall_never_exceeds_100_percent_when_chunks_share_provenance():
    """Regression test: a fragmented strategy where several small chunks
    all trace back to the same original section must not inflate recall
    past what's warranted - recall counts distinct target ids covered,
    not how many retrieved chunks happened to overlap one of them."""
    retrieved = [
        ExperimentChunk(content="a", provenance={"topic-a"}),
        ExperimentChunk(content="b", provenance={"topic-a"}),
        ExperimentChunk(content="c", provenance={"topic-a"}),
    ]
    precision, recall = _precision_recall_at_k(retrieved, {"topic-a"}, k=3)
    assert recall == 1.0  # not 3.0
    assert precision == 1.0


def test_mrr_finds_the_first_chunk_whose_provenance_overlaps():
    retrieved = [
        ExperimentChunk(content="a", provenance={"x"}),
        ExperimentChunk(content="b", provenance={"y", "z"}),
    ]
    assert _mrr(retrieved, {"z"}) == 0.5
    assert _mrr(retrieved, {"x"}) == 1.0
    assert _mrr(retrieved, {"nowhere"}) == 0.0
