from eval.metrics.retrieval import _mrr, _precision_recall_at_k, evaluate_retrieval


def test_precision_recall_at_k_with_controlled_inputs():
    retrieved = ["a", "b", "c", "d", "e"]
    relevant = {"b", "e", "z"}  # z is relevant but never retrieved

    precision, recall = _precision_recall_at_k(retrieved, relevant, k=3)
    assert precision == 1 / 3  # only "b" in top 3
    assert recall == 1 / 3  # 1 of 3 relevant chunks found

    precision5, recall5 = _precision_recall_at_k(retrieved, relevant, k=5)
    assert precision5 == 2 / 5  # b and e in top 5
    assert recall5 == 2 / 3


def test_mrr_rewards_earlier_hits():
    assert _mrr(["a", "b", "c"], {"a"}) == 1.0
    assert _mrr(["a", "b", "c"], {"b"}) == 0.5
    assert _mrr(["a", "b", "c"], {"c"}) == 1 / 3
    assert _mrr(["a", "b", "c"], {"z"}) == 0.0


def test_evaluate_retrieval_against_the_real_ingested_corpus(db_session):
    questions = [
        {
            "id": "test-1",
            "question": "What is the 50/30/20 budgeting rule?",
            "relevant_chunks": ["budgeting-50-30-20"],
        },
        {
            "id": "test-2",
            "question": "This has no relevant_chunks and should be excluded",
            "relevant_chunks": [],
        },
    ]

    result = evaluate_retrieval(db_session, questions)

    assert result["summary"]["questions_scored"] == 1  # test-2 excluded, empty relevant_chunks
    assert result["per_question"][0]["id"] == "test-1"
    assert result["per_question"][0]["recall@3"] == 1.0  # the obvious-query case, already verified in test_rag_retrieval.py
