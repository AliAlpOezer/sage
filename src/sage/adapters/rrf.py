"""Reciprocal Rank Fusion — Day-36 hybrid-search drill.

Combines the dense (`VectorStore.search`) and sparse (`SparseRetriever.search`,
e.g. BM25) ranked lists into one fused ranking. This is the hand-written half
of hybrid search: `fuse` is the whole exercise, deliberately left
unimplemented below. Everything around it — the BM25 adapter
(`sage.adapters.bm25_store`), the `hybrid` eval variant
(`sage.evals.harness`), and the `service.answer` wiring that calls this
function — is already wired and runnable; only this function raises.

The executable spec for `fuse` lives in `tests/test_rrf.py`: those tests are
marked `xfail(raises=NotImplementedError, strict=True)` and must pass,
unmodified, once this is implemented (a still-passing xfail — i.e. `fuse` no
longer raises but a test still fails — means the implementation is wrong).
"""

from collections.abc import Sequence


def fuse(ranked_lists: Sequence[Sequence[str]], k: int = 60) -> list[tuple[str, float]]:
    """Fuse multiple ranked retrieval lists into one ranking via RRF.

    Args:
        ranked_lists: One ranked list per retrieval method that took part in
            this query (e.g. `[dense_ids, sparse_ids]` for dense + BM25 hybrid
            search, but the function must work for any number of lists >= 1,
            including a single list). Each inner list is a sequence of
            document/chunk ids (the same ids `Chunk.id` uses), ordered
            best-first: the id at index 0 is that method's top-ranked result,
            the id at index 1 is its second-ranked result, and so on. A given
            id may appear in some lists and not others (e.g. BM25 found a
            keyword match dense search missed, or vice versa) — that is the
            whole point of fusing. A given id never repeats within one inner
            list. Lists may differ in length from each other.
        k: The RRF constant (default 60, the standard value from the original
            paper — "Reciprocal Rank Fusion outperforms Condorcet and
            individual rank learning methods", Cormack et al. 2009). It is
            added to the rank before inverting, which dampens how much a
            document's score is dominated by a #1 placement in any single
            list: with a small k, rank 1 vs. rank 2 in one list swings the
            score far more than with a large k, where the difference between
            neighboring ranks is relatively small and a document has to rank
            well across *multiple* lists to score highly. `k` is the same
            constant for every list and every document — it is not tuned per
            list.

    Returns:
        A list of `(doc_id, fused_score)` tuples, one entry per *distinct*
        document id that appears in at least one input list (so the output
        length is the size of the union of all input lists, not the sum),
        ordered best-first: descending by `fused_score`. Ties (equal fused
        score) break by the document's best (lowest) rank in any single input
        list, and if still tied, by the order the id first appears across
        `ranked_lists` (earlier list first, then earlier rank within that
        list) — i.e. the ordering must be deterministic and reproducible for
        the same input, not dependent on set/dict iteration order.

    Formula (the actual fusion, stated in words — implement exactly this, not
    an approximation of it):
        For every document id that appears anywhere in `ranked_lists`, its
        fused score is the SUM, over every input list that contains it, of
        1 / (k + r), where r is that document's 1-indexed rank *within that
        particular list* (the top-ranked entry of a list has r = 1, not r =
        0). A document that does not appear in a given list contributes
        nothing to its score from that list — it is not treated as ranked
        last, and the missing list is not backfilled with a default rank.
        A document appearing in every list accumulates one 1/(k+r) term per
        list; a document appearing in only one list gets a single term.
        There is no normalization step beyond this sum: the returned
        `fused_score` values are the raw sums, not rescaled to [0, 1].
    """
    if len(ranked_lists) == 0:
        return []

    scores: dict[str, float] = {}
    best_rank: dict[str, int] = {}
    first_seen: dict[str, tuple[int, int]] = {}

    for list_idx, ranked_list in enumerate(ranked_lists):
        for pos, doc_id in enumerate(ranked_list):
            rank = pos + 1
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

            if doc_id not in best_rank or rank < best_rank[doc_id]:
                best_rank[doc_id] = rank

            if doc_id not in first_seen:
                first_seen[doc_id] = (list_idx, rank)

    def sort_key(doc_id: str) -> tuple[float, int, int, int]:
        # descending score -> ascending best_rank -> ascending first_seen(list_idx,rank)
        return (
            -scores[doc_id],
            best_rank[doc_id],
            first_seen[doc_id][0],
            first_seen[doc_id][1],
        )

    ordered_ids = sorted(scores.keys(), key=sort_key)
    return [(doc_id, scores[doc_id]) for doc_id in ordered_ids]