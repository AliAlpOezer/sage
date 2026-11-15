from sage.adapters import bm25_store
from sage.config import Settings
from sage.models import Chunk


class _Point:
    def __init__(self, chunk: Chunk):
        self.id = chunk.id
        self.payload = {
            "text": chunk.text,
            "source_url": chunk.source_url,
            "title": chunk.title,
            "position": chunk.position,
        }


class _FakeClient:
    """Mimics QdrantClient.scroll: one page of results, then (empty, None)."""

    def __init__(self, chunks: list[Chunk]):
        self._chunks = chunks
        self.scroll_calls = 0

    def scroll(self, collection_name, limit, offset, with_payload):
        self.scroll_calls += 1
        if offset is not None:
            return [], None
        return [_Point(c) for c in self._chunks], None


class _FakeStore:
    def __init__(self, chunks: list[Chunk]):
        self.client = _FakeClient(chunks)


def _retriever(monkeypatch, chunks: list[Chunk]) -> tuple[bm25_store.Bm25Retriever, _FakeStore]:
    store = _FakeStore(chunks)
    monkeypatch.setattr(bm25_store, "make_vector_store", lambda settings: store)
    return bm25_store.Bm25Retriever(Settings()), store


def test_ranks_exact_keyword_match_first(monkeypatch):
    chunks = [
        Chunk(id="a", text="qdrant vector database search", source_url="u", title="T", position=0),
        Chunk(id="b", text="completely unrelated banana bread recipe", source_url="u", title="T", position=1),
    ]
    retriever, _ = _retriever(monkeypatch, chunks)
    results = retriever.search("qdrant vector search", k=2)
    assert results[0].chunk.id == "a"


def test_search_respects_k_limit(monkeypatch):
    chunks = [
        Chunk(id=str(i), text=f"term{i} shared word", source_url="u", title="T", position=i)
        for i in range(5)
    ]
    retriever, _ = _retriever(monkeypatch, chunks)
    results = retriever.search("shared word", k=2)
    assert len(results) == 2


def test_empty_corpus_returns_empty(monkeypatch):
    retriever, _ = _retriever(monkeypatch, [])
    assert retriever.search("anything", k=5) == []


def test_index_builds_once(monkeypatch):
    chunks = [Chunk(id="a", text="hello world", source_url="u", title="T", position=0)]
    retriever, store = _retriever(monkeypatch, chunks)
    retriever.search("hello", k=1)
    retriever.search("world", k=1)
    # scroll() is called until it returns offset=None; a fresh build per
    # search would double this count.
    assert store.client.scroll_calls == 1
