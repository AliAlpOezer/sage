"""The ports: interfaces every backend must satisfy.

Swapping a backend (OpenRouter -> local model, Qdrant -> pgvector) means
writing one adapter that satisfies the Protocol and registering it with the
factory; nothing else in the pipeline changes.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from sage.graph.schema import Edge, Node, NodeType
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
class SparseRetriever(Protocol):
    def search(self, query: str, k: int) -> list[ScoredChunk]:
        """Keyword-match `query` against the corpus; return top-k, best-first.

        The lexical counterpart to `VectorStore.search` (semantic/dense). Used
        for hybrid retrieval: the caller runs both and fuses the two ranked
        lists (see `sage.adapters.rrf.fuse`) rather than trusting either alone.
        """
        ...


@runtime_checkable
class Reranker(Protocol):
    def rerank(self, question: str, chunks: Sequence[ScoredChunk]) -> list[ScoredChunk]:
        """Re-score `chunks` against `question` and return them sorted best-first.

        Day-37 precision stage: the first-stage retriever fetches a wide candidate
        set (`settings.retrieve_k`); this reorders it with an accurate cross-encoder.
        The returned `ScoredChunk.score` carries the reranker's relevance score
        (not the original vector similarity), and the caller keeps only the top
        `settings.top_k`. Returning fewer than given is allowed; returning more is not.
        """
        ...


class EmptyIndex(RuntimeError):
    """A strategy's store holds nothing to retrieve: its build/ingest hasn't run."""


@runtime_checkable
class RetrievalStrategy(Protocol):
    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        """Return the `k` chunks this strategy judges best for `question`, best-first.

        Each strategy answers from its own store alone and never calls another
        strategy, so a score can be attributed to it. A strategy that cannot
        answer raises; there is no silent fallback to another strategy.
        """
        ...


class GraphUnavailable(RuntimeError):
    """The graph database cannot be reached (not configured, paused, or down)."""


class GraphQueryError(RuntimeError):
    """The graph database refused a query: bad syntax, unknown name, a write in a read, ..."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@runtime_checkable
class GraphStore(Protocol):
    """A property graph that builders fill and graph strategies query.

    Writes are keyed merges stamped with a `build_id`, so a build can be repeated
    and anything an earlier build left behind can be pruned afterwards. Queries are
    hand-written Cypher and go through `read`, which can never write.
    """

    def ensure_constraints(self) -> None:
        """Create the uniqueness constraint of every schema node type, if missing."""
        ...

    def ensure_vector_index(self, dimension: int) -> None:
        """Create the chunk vector index, or raise if one exists with another dimension."""
        ...

    def keys(self, node_type: NodeType, where: Mapping[str, Any]) -> set[str]:
        """Keys of the nodes of `node_type` whose properties equal every item of `where`."""
        ...

    def merge_nodes(self, nodes: Sequence[Node], build_id: str) -> None:
        """Insert or update by key. Properties not named in a node are left as they are."""
        ...

    def merge_edges(self, edges: Sequence[Edge], build_id: str) -> None:
        """Insert or update by (type, source, target). Both end nodes must exist."""
        ...

    def prune(self, namespace: str, build_id: str) -> int:
        """Delete what `namespace` holds from any other build; returns how many items."""
        ...

    def read(self, cypher: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run a query in a read-only transaction, one dict per result row.

        A query that tries to write fails, whoever wrote it (graph.md G12).
        """
        ...


@runtime_checkable
class Generator(Protocol):
    def generate(self, question: str, context: Sequence[ScoredChunk]) -> str:
        """Answer the question grounded only in the given context chunks."""
        ...


@runtime_checkable
class ChatModel(Protocol):
    def complete(self, system: str, user: str) -> str:
        """One chat completion: the model's reply to `user` under the `system` prompt."""
        ...
