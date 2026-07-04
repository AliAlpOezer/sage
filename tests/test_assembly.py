from sage.assembly import arrange
from sage.models import Chunk, ScoredChunk


def scored(i: int, score: float) -> ScoredChunk:
    return ScoredChunk(
        chunk=Chunk(id=str(i), text=f"t{i}", source_url="u", title="T", position=i),
        score=score,
    )


def test_empty_and_single():
    assert arrange([]) == []
    one = [scored(1, 0.9)]
    assert arrange(one) == one


def test_best_first_second_best_last():
    ranked = [scored(i, 1.0 - i / 10) for i in range(1, 6)]  # 1 strongest .. 5 weakest
    result = arrange(ranked)
    assert result[0] == ranked[0], "strongest chunk must open the context"
    assert result[-1] == ranked[1], "second-strongest must close the context"
    positions = [r.chunk.position for r in result]
    assert positions == [1, 3, 5, 4, 2]


def test_nothing_lost_or_duplicated():
    ranked = [scored(i, 1.0 - i / 10) for i in range(1, 8)]
    result = arrange(ranked)
    assert sorted(r.chunk.position for r in result) == list(range(1, 8))
