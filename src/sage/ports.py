"""The ports: interfaces every backend must satisfy.

Swapping a backend (OpenRouter -> local model, Qdrant -> pgvector) means
writing one adapter that satisfies the Protocol and registering it with the
factory; nothing else in the pipeline changes.
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from sage.models import Chunk, Page, ScoredChunk


@runtime_checkable
class Chunker(Protocol):
    def chunk(self, page: Page) -> list[Chunk]:
        """Split one page into retrieval-sized chunks, in document order."""
        ...


@runtime_checkable
class Embedder(Protocol):
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of texts. Result order matches input order.

        Vector dimension is discovered from the result (len(vectors[0])),
        not declared up front — one less thing to configure per model.
        """
        ...


@runtime_checkable
class VectorStore(Protocol):
    def ensure_collection(self, dimension: int) -> None:
        """Create the collection if missing; no-op if it already exists."""
        ...

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Insert or overwrite by chunk id — re-ingesting must not duplicate."""
        ...

    def search(self, vector: Sequence[float], k: int) -> list[ScoredChunk]: ...

    def count(self) -> int: ...


@runtime_checkable
class Generator(Protocol):
    def generate(self, question: str, context: Sequence[ScoredChunk]) -> str:
        """Answer the question grounded only in the given context chunks."""
        ...
