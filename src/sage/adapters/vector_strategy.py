"""RetrievalStrategy adapter: the Qdrant-backed retrieval flow, as one strategy.

Dense search, then optionally BM25 fused with it by RRF (`sparse_retriever`), then
the reranker (`reranker`, passthrough when "none"). The baseline, hybrid, rerank and
hybrid-rerank eval variants are all this one strategy under different settings; the
graph strategies are its siblings and never call it (see `docs/context/graph.md`).
"""

import asyncio

from sage.adapters.rrf import fuse
from sage.config import Settings
from sage.factory import (
    make_embedder,
    make_reranker,
    make_sparse_retriever,
    make_vector_store,
    register_strategy,
)
from sage.models import ScoredChunk
from sage.ports import EmptyIndex


@register_strategy("vector")
class VectorStrategy:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedder = make_embedder(settings)
        self.store = make_vector_store(settings)
        self.reranker = make_reranker(settings)

    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        settings = self.settings
        if self.store.count() == 0:
            raise EmptyIndex("vector store is empty - run: uv run python -m sage.ingest")

        query_vector = asyncio.run(self.embedder.embed([question]))[0]
        # With a reranker and/or sparse retriever active, fetch a wide candidate set
        # (retrieve_k) so fusion and the cross-encoder have a real pool to select
        # from; with both "none" the widen is a no-op.
        widen = settings.reranker != "none" or settings.sparse_retriever != "none"
        fetch_k = max(k, settings.retrieve_k) if widen else k
        dense_hits = self.store.search(query_vector, fetch_k)

        if settings.sparse_retriever != "none":
            # Day-36 hybrid search: a second, lexical ranked list fused with the
            # dense one by Reciprocal Rank Fusion (`fuse`, the hand-written drill).
            sparse_hits = make_sparse_retriever(settings).search(question, fetch_k)
            by_id = {sc.chunk.id: sc.chunk for sc in (*dense_hits, *sparse_hits)}
            fused = fuse(
                [
                    [sc.chunk.id for sc in dense_hits],
                    [sc.chunk.id for sc in sparse_hits],
                ]
            )
            hits = [ScoredChunk(chunk=by_id[doc_id], score=score) for doc_id, score in fused]
        else:
            hits = dense_hits

        return self.reranker.rerank(question, hits)[:k]
