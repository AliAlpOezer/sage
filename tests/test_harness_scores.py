import json
import math

from sage.evals.harness import (
    MAX_SCORE_ATTEMPTS,
    _load_scores,
    _merge_score,
    _score_complete,
)
from sage.evals.scorecard import METRIC_COLS

FULL = dict.fromkeys(METRIC_COLS, 0.5)


def test_merge_keeps_earlier_values_and_fills_gaps():
    first = _merge_score(None, "e001", "j", {**FULL, "context_recall": math.nan})
    assert first["context_recall"] is None and first["attempts"] == 1
    assert not _score_complete(first)
    second = _merge_score(first, "e001", "j", {**dict.fromkeys(METRIC_COLS, 0.9)})
    assert second["faithfulness"] == 0.5  # kept from attempt 1
    assert second["context_recall"] == 0.9  # filled by attempt 2
    assert second["attempts"] == 2 and _score_complete(second)


def test_persistent_nan_is_accepted_after_max_attempts():
    row = None
    for _ in range(MAX_SCORE_ATTEMPTS):
        row = _merge_score(row, "u001", "j", {**FULL, "answer_relevancy": math.nan})
    assert row["answer_relevancy"] is None and _score_complete(row)


def test_scores_from_another_judge_are_ignored_and_latest_row_wins(tmp_path):
    path = tmp_path / "scores.jsonl"
    rows = [
        _merge_score(None, "e001", "old-judge", FULL),
        _merge_score(None, "e002", "new-judge", {**FULL, "faithfulness": math.nan}),
        _merge_score(None, "e002", "new-judge", FULL),
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    loaded = _load_scores(path, "new-judge")
    assert set(loaded) == {"e002"}
    assert loaded["e002"]["faithfulness"] == 0.5
