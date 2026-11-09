"""Reranker adapters (Day-37 precision stage).

Three backends:
  - "none": passthrough. Returns the first-stage order untouched, so the baseline
    pipeline behaves exactly as before this stage existed. This is the reference arm.
  - "bge": local cross-encoder (BAAI/bge-reranker-v2-m3 via sentence-transformers).
    BLOCKED on this machine — segfaults when `qdrant_client` is imported in-process
    alongside torch (see docs/context/gotchas.md). Left in place for when that's fixed.
  - "cohere": hosted Rerank v2 API (https://api.cohere.com/v2/rerank). No local model,
    so it sidesteps the bge/qdrant conflict entirely.
"""

import time
from collections.abc import Sequence

import httpx
import numpy as np

from sage.config import Settings
from sage.factory import register_reranker
from sage.models import ScoredChunk


@register_reranker("none")
class PassthroughReranker:
    """No-op: keeps first-stage order. The baseline arm of the A/B."""

    def __init__(self, settings: Settings):
        pass

    def rerank(self, question: str, chunks: Sequence[ScoredChunk]) -> list[ScoredChunk]:
        return list(chunks)


@register_reranker("bge")
class BgeReranker:
    """Cross-encoder reranker over a local BGE model.

    Scaffolding provided: lazy model load + the port contract. The scoring and
    top-k selection are yours to write (Day-37 drill: "top-k reranking selection
    with pure NumPy").
    """

    def __init__(self, settings: Settings):
        # Model name kept here so a bigger/smaller BGE variant is a one-line swap.
        self.model_name = "BAAI/bge-reranker-v2-m3"
        self._model = None  # lazily loaded on first rerank() — import cost stays off the baseline path

    def _load(self):
        if self._model is None:
            # sentence-transformers is an optional dep (see pyproject `rerank` group):
            #   uv sync --group rerank
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, question: str, chunks: Sequence[ScoredChunk]) -> list[ScoredChunk]:
        # ── YOUR CORE (Day-37) ─────────────────────────────────────────────
        # Contract (see ports.Reranker):
        #   1. Build (question, chunk.text) pairs for every chunk.
        if not chunks: 
            return []

        pairs = [(question, c.chunk.text) for c in chunks]

        #   2. model = self._load(); scores = model.predict(pairs)  # cross-encoder relevance
        model = self._load()
        scores = model.predict(pairs)
        #   3. Sort chunks by score descending — do the selection with NumPy argsort
        #      (that is the drill). Return list[ScoredChunk] with the NEW score:
        #      ScoredChunk(chunk=c.chunk, score=float(s)).
        order = np.argsort(scores)[::-1]
        #   4. Return best-first. The caller slices [:top_k]; you may return all of them.
        # Keep it pure/vectorized; no I/O beyond the model call.
        return [
            ScoredChunk(
                chunk = chunks[i].chunk,
                score = float(scores[i]),
            )
            for i in order
        ]
        # ───────────────────────────────────────────────────────────────────


_COHERE_URL = "https://api.cohere.com/v2/rerank"


@register_reranker("cohere")
class CohereReranker:
    """Hosted cross-encoder via Cohere Rerank v2. No local model — the fix for the
    bge/qdrant_client in-process conflict (see docs/context/gotchas.md)."""

    def __init__(self, settings: Settings):
        self.api_key = settings.cohere_api_key
        self.model = settings.cohere_rerank_model

    def rerank(self, question: str, chunks: Sequence[ScoredChunk]) -> list[ScoredChunk]:
        if not chunks:
            return []
        if not self.api_key:
            raise ValueError("COHERE_API_KEY is not set (required for reranker=cohere)")

        documents = [c.chunk.text for c in chunks]
        payload = {"model": self.model, "query": question, "documents": documents}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=60, headers=headers) as client:
            for attempt in (1, 2, 3):
                response = client.post(_COHERE_URL, json=payload)
                if response.status_code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                response.raise_for_status()
                break

        results = response.json()["results"]  # sorted by relevance_score, descending
        return [
            ScoredChunk(chunk=chunks[r["index"]].chunk, score=float(r["relevance_score"]))
            for r in results
        ]
