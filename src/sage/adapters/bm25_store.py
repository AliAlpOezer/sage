"""SparseRetriever adapter: BM25 keyword search over the ingested corpus.

Day-36 hybrid-search half: BM25 gives an orthogonal (lexical, exact-term)
signal to fuse with the dense VectorStore's semantic one via
`sage.adapters.rrf.fuse`, targeting the context_recall gap the baseline
scorecard shows (dense search misses exact-term queries embeddings blur).

Reuses the *cached* Qdrant client from `make_vector_store` rather than opening
a second `QdrantClient` on the same path — embedded Qdrant file-locks its
storage dir per process (see `factory.py`'s `_VECTOR_STORE_CACHE` comment and
`docs/context/gotchas.md`); a second live client for the same collection in
the same process would contend for that lock.
"""

import re

from rank_bm25 import BM25Okapi

from sage.config import Settings
from sage.factory import make_vector_store, register_sparse_retriever
from sage.models import Chunk, ScoredChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@register_sparse_retriever("bm25")
class Bm25Retriever:
    """Keyword retriever over the same corpus the dense VectorStore holds.

    The index is built lazily, on first `search()`, by scrolling every point
    out of the (already-open, cached) Qdrant collection once and tokenizing
    its text — so a request that never uses hybrid retrieval never pays for
    it. Rebuilding is O(collection size); fine for this corpus, would need a
    persisted/incremental index for anything larger.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Chunk] = []

    def _ensure_index(self) -> None:
        if self._bm25 is not None:
            return
        client = make_vector_store(self.settings).client
        collection = self.settings.collection
        chunks: list[Chunk] = []
        offset = None
        while True:
            points, offset = client.scroll(
                collection_name=collection, limit=256, offset=offset, with_payload=True
            )
            for p in points:
                chunks.append(
                    Chunk(
                        id=str(p.id),
                        text=p.payload["text"],
                        source_url=p.payload["source_url"],
                        title=p.payload["title"],
                        position=p.payload["position"],
                    )
                )
            if offset is None:
                break
        self._chunks = chunks
        self._bm25 = BM25Okapi([_tokenize(c.text) for c in chunks]) if chunks else None

    def search(self, query: str, k: int) -> list[ScoredChunk]:
        self._ensure_index()
        if not self._chunks:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [ScoredChunk(chunk=self._chunks[i], score=float(scores[i])) for i in order]
