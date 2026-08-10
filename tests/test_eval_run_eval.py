"""Only save_result is unit-tested here - run_eval() itself makes 18 real
LLM calls against seeded persona data and belongs to manual/CI-scheduled
runs, not the fast test suite (same reasoning as eval/ingest.py and
eval/seed_persona.py having no dedicated "run the whole thing" test).
"""

import pytest

from eval.run_eval import save_result


def test_never_overwrites_an_existing_result(tmp_path, monkeypatch):
    import eval.run_eval as run_eval_module

    monkeypatch.setattr(run_eval_module, "RESULTS_DIR", tmp_path)

    save_result({"label": "first"}, "test.json")
    with pytest.raises(FileExistsError):
        save_result({"label": "second"}, "test.json")

    import json
    saved = json.loads((tmp_path / "test.json").read_text())
    assert saved["label"] == "first"  # untouched by the second, rejected attempt
