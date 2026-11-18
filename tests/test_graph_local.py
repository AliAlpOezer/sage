from dataclasses import replace

import pytest

from sage import factory
from sage.adapters import graph_local
from sage.adapters.graph_local import GraphLocalStrategy, support
from sage.config import Settings
from sage.graph.current import BUILD_QUERY, StaleGraph
from sage.ports import EmptyIndex, RetrievalStrategy

BUILD_ROW = {"snapshot": "snap", "snapshot_id": "abc", "embedding_model": "model-a"}


class FakeGraph:
    """Answers the strategy's queries from canned rows; anything else is a test failure."""

    def __init__(self, seeds, edges, build=BUILD_ROW):
        self.seeds = seeds  # id -> similarity
        self.edges = edges  # (seed, candidate, weight, similarity)
        self.build = build
        self.reads: list[str] = []
        self.seed_n: int | None = None

    def read(self, cypher, params=None):
        self.reads.append(cypher)
        if cypher == BUILD_QUERY:
            return [self.build] if self.build else []
        if cypher == graph_local.SEED_QUERY:
            self.seed_n = params["n"]
            ranked = sorted(self.seeds.items(), key=lambda kv: -kv[1])[: params["n"]]
            return [{"id": i, "similarity": s} for i, s in ranked]
        if cypher == graph_local.EXPAND_QUERY:
            return [
                {"seed": s, "candidate": c, "weight": w, "similarity": sim}
                for s, c, w, sim in self.edges
                if s in params["seeds"]
            ]
        if cypher == graph_local.FETCH_QUERY:
            return [
                {
                    "id": i,
                    "text": f"text {i}",
                    "source_url": f"https://x/{i}.md",
                    "title": i,
                    "position": 0,
                }
                for i in params["ids"]
            ]
        raise AssertionError(f"unexpected query: {cypher}")


_GRAPH = FakeGraph({}, [])


@factory.register_graph_store("fake-graph-test")
def _fake_graph(settings: Settings) -> FakeGraph:
    return _GRAPH


@factory.register_embedder("unit-test")
class UnitEmbedder:
    def __init__(self, settings: Settings):
        pass

    async def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


@factory.register_vector_store("raising-test")
def _raising_store(settings: Settings):
    raise AssertionError(
        "a graph strategy must never build the vector store (graph.md invariant 1)"
    )


def _settings(**overrides) -> Settings:
    base = {
        "strategy": "graph-local",
        "graph_store": "fake-graph-test",
        "neo4j_uri": "fake://graph-local-test",
        "embedder": "unit-test",
        "embedding_model": "model-a",
        "vector_store": "raising-test",
        "snapshot": "snap",
        "graph_seed_k": 3,
    }
    return Settings(**{**base, **overrides})


@pytest.fixture
def graph():
    # The factory caches graph stores per connection, so reset the one instance in place.
    # Seeds a, b, c by similarity. "bridge" is reached from both a and b but sits below
    # every seed in similarity; "c" is a seed nothing else points at.
    _GRAPH.__init__(
        seeds={"a": 0.90, "b": 0.85, "c": 0.84, "d": 0.10},
        edges=[
            ("a", "bridge", 1.0, 0.70),
            ("b", "bridge", 0.7, 0.70),
            ("a", "b", 0.4, 0.85),
            ("b", "a", 0.4, 0.90),
            ("c", "lonely", 0.1, 0.20),
        ],
    )
    return _GRAPH


def test_support_sums_over_seeds_weighted_by_seed_similarity():
    seeds = {"s1": 0.8, "s2": 0.5}
    got = support(
        seeds, [("s1", "x", 1.0), ("s2", "x", 0.5), ("s1", "y", 0.4), ("s1", "s1", 1.0)]
    )
    assert got == pytest.approx({"x": 0.8 + 0.25, "y": 0.32})


def test_strategy_satisfies_the_port(graph):
    assert isinstance(factory.make_strategy(_settings()), RetrievalStrategy)


def test_a_chunk_two_seeds_point_at_outranks_an_unsupported_seed(graph):
    hits = GraphLocalStrategy(_settings()).retrieve("q", 3)
    assert [h.chunk.id for h in hits] == ["a", "b", "bridge"]
    assert hits[2].chunk.text == "text bridge"
    assert hits[0].score > hits[1].score > hits[2].score


def test_seed_count_is_at_least_k(graph):
    GraphLocalStrategy(_settings(graph_seed_k=1)).retrieve("q", 5)
    assert graph.seed_n == 5


def test_answers_without_the_vector_store(graph):
    # The vector store's factory raises, so any path through Qdrant would fail here.
    hits = factory.make_strategy(_settings()).retrieve("q", 2)
    assert len(hits) == 2


def test_unbuilt_graph_raises_empty_index(graph):
    graph.build = None
    with pytest.raises(EmptyIndex, match="sage.graph.build"):
        GraphLocalStrategy(_settings()).retrieve("q", 3)


def test_graph_from_another_snapshot_is_refused(graph):
    with pytest.raises(StaleGraph, match="'snap', not 'other'"):
        GraphLocalStrategy(_settings(snapshot="other")).retrieve("q", 3)


def test_graph_embedded_with_another_model_is_refused(graph):
    with pytest.raises(StaleGraph, match="model-a"):
        GraphLocalStrategy(_settings(embedding_model="model-b")).retrieve("q", 3)


def test_without_a_pinned_snapshot_any_build_is_served(graph):
    hits = GraphLocalStrategy(replace(_settings(), snapshot="")).retrieve("q", 1)
    assert [h.chunk.id for h in hits] == ["a"]


def test_every_query_is_a_read_scoped_to_the_structural_namespace(graph):
    GraphLocalStrategy(_settings()).retrieve("q", 3)
    for cypher in (graph_local.EXPAND_QUERY, graph_local.FETCH_QUERY):
        assert ":`Chunk`:`Structural`" in cypher
    writes = ("CREATE", "MERGE", "DELETE", " SET ", "REMOVE")
    assert not any(w in q.upper() for q in graph.reads for w in writes)
