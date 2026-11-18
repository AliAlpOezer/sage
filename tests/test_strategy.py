import pytest

from sage import factory, service
from sage.config import Settings
from sage.models import Chunk, ScoredChunk
from sage.ports import EmptyIndex, RetrievalStrategy


def _hit(i: int, score: float) -> ScoredChunk:
    text = f"chunk {i}"
    url = f"https://x/{i}.md"
    chunk = Chunk(id=Chunk.make_id(url, text), text=text, source_url=url, title=f"t{i}", position=0)
    return ScoredChunk(chunk=chunk, score=score)


@factory.register_generator("echo-test")
class EchoGenerator:
    def __init__(self, settings: Settings):
        pass

    def generate(self, question, context):
        return " ".join(sc.chunk.text for sc in context)


@factory.register_strategy("fixed-test")
class FixedStrategy:
    def __init__(self, settings: Settings):
        pass

    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        return [_hit(i, 1.0 - i / 10) for i in range(k)]


@factory.register_strategy("broken-test")
class BrokenStrategy:
    def __init__(self, settings: Settings):
        pass

    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        raise ConnectionError("store down")


@factory.register_embedder("const-test")
class ConstEmbedder:
    def __init__(self, settings: Settings):
        pass

    async def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


class FakeStore:
    def __init__(self, hits: list[ScoredChunk]):
        self.hits = hits
        self.asked_k: int | None = None

    def ensure_collection(self, dimension):
        pass

    def upsert(self, chunks, vectors):
        pass

    def search(self, vector, k):
        self.asked_k = k
        return self.hits[:k]

    def count(self):
        return len(self.hits)


_STORE = FakeStore([])


@factory.register_vector_store("fake-test")
def _fake_store(settings: Settings) -> FakeStore:
    return _STORE


@factory.register_reranker("reverse-test")
class ReverseReranker:
    def __init__(self, settings: Settings):
        pass

    def rerank(self, question, chunks):
        return list(reversed(chunks))


def _settings(**overrides) -> Settings:
    base = {"generator": "echo-test", "top_k": 3}
    return Settings(**{**base, **overrides})


@pytest.fixture(autouse=True)
def _clean_store_cache():
    factory.reset_vector_store_cache()
    yield
    factory.reset_vector_store_cache()


def test_answer_names_the_strategy_that_produced_it():
    result = service.answer("q", settings=_settings(strategy="fixed-test"))
    assert result.strategy == "fixed-test"
    assert len(result.sources) == 3
    assert [s.n for s in result.sources] == [1, 2, 3]


def test_failing_strategy_raises_instead_of_falling_back():
    with pytest.raises(ConnectionError, match="store down"):
        service.answer("q", settings=_settings(strategy="broken-test"))


def test_unknown_strategy_lists_the_available_ones():
    with pytest.raises(ValueError, match=r"Unknown strategy 'nope'.*vector"):
        service.answer("q", settings=_settings(strategy="nope"))


def _vector_settings(**overrides) -> Settings:
    return _settings(
        strategy="vector",
        embedder="const-test",
        vector_store="fake-test",
        collection="strategy-test",
        **overrides,
    )


def test_vector_strategy_satisfies_the_port():
    _STORE.hits = [_hit(0, 0.9)]
    strategy = factory.make_strategy(_vector_settings())
    assert isinstance(strategy, RetrievalStrategy)


def test_vector_strategy_dense_only_fetches_exactly_k():
    _STORE.hits = [_hit(i, 1.0 - i / 10) for i in range(10)]
    strategy = factory.make_strategy(_vector_settings())
    hits = strategy.retrieve("q", 3)
    assert _STORE.asked_k == 3
    assert [h.chunk.text for h in hits] == ["chunk 0", "chunk 1", "chunk 2"]


def test_vector_strategy_reranks_the_wide_pool_then_cuts_to_k():
    _STORE.hits = [_hit(i, 1.0 - i / 10) for i in range(10)]
    strategy = factory.make_strategy(_vector_settings(reranker="reverse-test", retrieve_k=8))
    hits = strategy.retrieve("q", 3)
    assert _STORE.asked_k == 8
    assert [h.chunk.text for h in hits] == ["chunk 7", "chunk 6", "chunk 5"]


def test_vector_strategy_on_empty_store_raises_empty_index():
    _STORE.hits = []
    strategy = factory.make_strategy(_vector_settings())
    with pytest.raises(EmptyIndex):
        strategy.retrieve("q", 3)
