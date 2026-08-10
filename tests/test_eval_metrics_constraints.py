from eval.metrics.constraints import check_constraints, evaluate_constraints


def test_passes_when_required_terms_present_and_forbidden_absent():
    question = {"id": "q1", "must_mention": ["trade-off"], "must_not_mention": ["guaranteed"]}
    result = check_constraints("This is a trade-off between risk and reward.", question)
    assert result["passed"] is True
    assert result["missing_required"] == []
    assert result["forbidden_present"] == []


def test_fails_when_required_term_missing():
    question = {"id": "q1", "must_mention": ["trade-off"]}
    result = check_constraints("Just buy the fund.", question)
    assert result["passed"] is False
    assert result["missing_required"] == ["trade-off"]


def test_fails_when_forbidden_term_present():
    question = {"id": "q1", "must_not_mention": ["guaranteed returns"]}
    result = check_constraints("This offers guaranteed returns.", question)
    assert result["passed"] is False
    assert result["forbidden_present"] == ["guaranteed returns"]


def test_case_insensitive_matching():
    question = {"id": "q1", "must_mention": ["Old Regime"]}
    result = check_constraints("this only applies under the old regime.", question)
    assert result["passed"] is True


def test_evaluate_constraints_only_scores_questions_with_constraints():
    questions = [
        {"id": "has-constraint", "must_mention": ["income"]},
        {"id": "no-constraint"},
    ]
    answers = {"has-constraint": "based on your income", "no-constraint": "anything"}

    result = evaluate_constraints(answers, questions)
    assert result["total"] == 1
    assert result["passed"] == 1
    assert result["pass_rate"] == 1.0
