import json
import math

import pandas as pd

from sage.evals.abstention import parse_verdict
from sage.evals.harness import (
    ABSTAINED,
    MAX_SCORE_ATTEMPTS,
    _answer_hash,
    _load_scores,
    _means,
    _merge_score,
    _score_complete,
    _source_hit,
)
from sage.evals.scorecard import METRIC_COLS


def test_source_hit_does_not_apply_when_the_context_cites_no_page():
    assert _source_hit(["https://x/a.md"], ["https://x/b.md", "https://x/a.md"]) == 1.0
    assert _source_hit(["https://x/a.md"], ["https://x/b.md"]) == 0.0
    assert _source_hit(["https://x/a.md"], [""]) is None  # text2cypher's query excerpt
    assert _source_hit([], ["https://x/a.md"]) is None

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


def test_score_of_a_regenerated_answer_is_not_reused(tmp_path):
    old = {"answer": "first", "retrieved_contexts": ["c"]}
    new = {"answer": "second", "retrieved_contexts": ["c"]}
    path = tmp_path / "scores.jsonl"
    row = _merge_score(None, "e001", "j", FULL, answer_hash=_answer_hash(old))
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert "e001" in _load_scores(path, "j", {"e001": _answer_hash(old)})
    assert _load_scores(path, "j", {"e001": _answer_hash(new)}) == {}


def test_unanswerable_row_is_complete_on_its_abstention_verdict_alone():
    row = _merge_score(None, "u001", "j", {ABSTAINED: 1.0}, cols=(ABSTAINED,))
    assert _score_complete(row, (ABSTAINED,))
    assert not _score_complete(row)  # it carries none of the RAGAS metrics


def test_means_ignore_unanswerable_rows():
    df = pd.DataFrame(
        [
            {"category": "easy", **dict.fromkeys(METRIC_COLS, 0.8), ABSTAINED: None},
            {"category": "unanswerable", **dict.fromkeys(METRIC_COLS, None), ABSTAINED: 1.0},
        ]
    )
    assert _means(df) == dict.fromkeys(METRIC_COLS, 0.8)


def test_abstention_verdict_takes_the_last_word_the_judge_says():
    assert parse_verdict("It could be ANSWERED, but no: DECLINED") == 1.0
    assert parse_verdict("answered") == 0.0
    assert parse_verdict("I am not sure.") is None
