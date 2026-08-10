import yaml
from pathlib import Path

from eval.metrics.routing import evaluate_routing

GOLDEN_QUESTIONS = Path(__file__).parent.parent / "eval" / "golden_questions.yaml"


def _load_questions():
    with open(GOLDEN_QUESTIONS) as f:
        return yaml.safe_load(f)["questions"]


def test_matches_the_known_94_percent_baseline():
    result = evaluate_routing(_load_questions())

    assert result["total"] == 36
    assert result["correct"] == 34
    assert result["accuracy"] == 34 / 36


def test_confusion_matrix_shows_the_two_known_misses():
    result = evaluate_routing(_load_questions())

    assert result["confusion_matrix"]["hybrid->sql"] == 2
    assert result["confusion_matrix"]["sql->sql"] == 10
    assert result["confusion_matrix"]["vector->vector"] == 10
    assert result["confusion_matrix"]["refuse->refuse"] == 6


def test_per_question_records_are_present_and_correctly_flagged():
    result = evaluate_routing(_load_questions())
    by_id = {r["id"]: r for r in result["per_question"]}

    assert by_id["sql-001"]["correct"] is True
    assert by_id["edge-003"]["correct"] is False
    assert by_id["edge-003"]["expected"] == "hybrid"
    assert by_id["edge-003"]["got"] == "sql"
