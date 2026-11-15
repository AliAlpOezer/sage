"""Executable spec for `sage.adapters.rrf.fuse` (Day-36 hand-written exercise).

These tests define correct behaviour per the formula in `rrf.py`'s docstring.
They are `xfail(raises=NotImplementedError, strict=True)`: they currently pass
*because* `fuse` raises `NotImplementedError` (strict xfail = "expected to
fail, and it must fail this exact way"). Once `fuse` is implemented, run this
file unmodified — every test must then pass for real (xfail -> pass flips
pytest's status to XPASS, which `strict=True` turns into a hard failure, so
"still marked xfail but the underlying assertions are wrong" is not a silent
pass).
"""

import pytest

from sage.adapters.rrf import fuse


def test_single_list_preserves_order_and_uses_1_over_k_plus_rank():
    result = fuse([["a", "b", "c"]], k=60)
    ids = [doc_id for doc_id, _ in result]
    assert ids == ["a", "b", "c"]
    scores = dict(result)
    assert scores["a"] == pytest.approx(1 / 61)
    assert scores["b"] == pytest.approx(1 / 62)
    assert scores["c"] == pytest.approx(1 / 63)


def test_doc_in_both_lists_outranks_doc_in_one():
    # "shared" is rank 2 in both lists -> 2/(k+2). "only_a" is rank 1 in one
    # list only -> 1/(k+1). With k=60, 2/62 (~0.0323) beats 1/61 (~0.0164).
    dense = ["only_a", "shared"]
    sparse = ["other", "shared"]
    result = fuse([dense, sparse], k=60)
    ids = [doc_id for doc_id, _ in result]
    assert ids.index("shared") < ids.index("only_a")


def test_score_is_exact_sum_of_reciprocal_ranks():
    dense = ["x", "y"]  # x rank 1, y rank 2
    sparse = ["y", "x"]  # y rank 1, x rank 2
    k = 10
    result = dict(fuse([dense, sparse], k=k))
    expected = 1 / (k + 1) + 1 / (
        k + 2
    )  # same for both: each is rank 1 in one, rank 2 in the other
    assert result["x"] == pytest.approx(expected)
    assert result["y"] == pytest.approx(expected)


def test_result_is_union_not_intersection():
    dense = ["a", "b"]
    sparse = ["c"]
    result = fuse([dense, sparse])
    assert {doc_id for doc_id, _ in result} == {"a", "b", "c"}


def test_empty_lists_yield_empty_result():
    assert fuse([[], []]) == []
    assert fuse([]) == []


def test_result_sorted_descending_by_fused_score():
    dense = ["a", "b", "c"]
    sparse = ["b", "a", "c"]
    result = fuse([dense, sparse])
    scores = [score for _, score in result]
    assert scores == sorted(scores, reverse=True)


def test_larger_k_compresses_the_score_gap_between_ranks():
    small_k = dict(fuse([["a", "b"]], k=1))
    large_k = dict(fuse([["a", "b"]], k=1000))
    gap_small = small_k["a"] - small_k["b"]
    gap_large = large_k["a"] - large_k["b"]
    assert gap_small > gap_large > 0
