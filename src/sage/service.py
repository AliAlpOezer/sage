"""Programmatic query loop shared by the CLI and the HTTP API.

`ask.py` printed its result; the UI needs it as data. This extracts the
embed -> top-k -> assemble -> generate loop into `answer()`, which returns the
generated text plus the structured source list (numbered to match the inline
[n] citations the generator emits). Each source carries its chunk `text` so the
UI's inspector panel can show what was actually retrieved.
"""

import asyncio
from dataclasses import dataclass

from sage.adapters.rrf import fuse
from sage.assembly import arrange
from sage.config import Settings
from sage.factory import (
    make_embedder,
    make_generator,
    make_reranker,
    make_sparse_retriever,
    make_vector_store,
)
from sage.models import ScoredChunk


@dataclass(frozen=True)
class Source:
    n: int  # matches the inline [n] citation in the answer
    title: str
    url: str
    score: float
    text: str


@dataclass(frozen=True)
class Answer:
    answer: str
    sources: list[Source]


class EmptyIndex(RuntimeError):
    """Raised when the vector store has no vectors — ingest hasn't been run."""


def answer(question: str, k: int | None = None, settings: Settings | None = None) -> Answer:
    settings = settings or Settings.from_env()
    k = k or settings.top_k
    embedder = make_embedder(settings)
    store = make_vector_store(settings)
    reranker = make_reranker(settings)
    generator = make_generator(settings)

    if store.count() == 0:
        raise EmptyIndex("vector store is empty — run: uv run python -m sage.ingest")

    query_vector = asyncio.run(embedder.embed([question]))[0]
    # With a reranker and/or sparse retriever active, fetch a wide candidate
    # set (retrieve_k) rather than exactly k, so there's a real pool for the
    # cross-encoder / fusion step to select from; with both "none" the widen
    # is a no-op (fetch exactly k).
    widen = settings.reranker != "none" or settings.sparse_retriever != "none"
    fetch_k = max(k, settings.retrieve_k) if widen else k
    dense_hits = store.search(query_vector, fetch_k)

    if settings.sparse_retriever != "none":
        # Day-36 hybrid search: fetch a second, lexical (BM25) ranked list and
        # fuse it with the dense one via Reciprocal Rank Fusion. `fuse` is the
        # hand-written exercise (sage.adapters.rrf) — this call raises
        # NotImplementedError until it's written; everything around it is wired.
        sparse = make_sparse_retriever(settings)
        sparse_hits = sparse.search(question, fetch_k)
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

    reranked = reranker.rerank(question, hits)
    context = arrange(reranked[:k], order=settings.assembly_order)
    text = generator.generate(question, context)

    sources = [
        Source(
            n=i,
            title=s.chunk.title,
            url=s.chunk.source_url,
            score=s.score,
            text=s.chunk.text,
        )
        for i, s in enumerate(context, start=1)
    ]
    return Answer(answer=text, sources=sources)
