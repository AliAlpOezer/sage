"""Config-keyed factories for the swappable components.

Each port has a registry mapping a short name (what goes in .env) to a builder.
Adapters register themselves at import time via the register_* decorators, so
adding a backend is: write the adapter, decorate it, set its name in .env.
"""

from collections.abc import Callable

from sage.config import Settings
from sage.ports import (
    ChatModel,
    Chunker,
    Embedder,
    Generator,
    GraphStore,
    Reranker,
    RetrievalStrategy,
    SparseRetriever,
    VectorStore,
)

_CHUNKERS: dict[str, Callable[[Settings], Chunker]] = {}
_EMBEDDERS: dict[str, Callable[[Settings], Embedder]] = {}
_VECTOR_STORES: dict[str, Callable[[Settings], VectorStore]] = {}
_SPARSE_RETRIEVERS: dict[str, Callable[[Settings], SparseRetriever]] = {}
_RERANKERS: dict[str, Callable[[Settings], Reranker]] = {}
_GENERATORS: dict[str, Callable[[Settings], Generator]] = {}
_STRATEGIES: dict[str, Callable[[Settings], RetrievalStrategy]] = {}
_GRAPH_STORES: dict[str, Callable[[Settings], GraphStore]] = {}

# Embedded qdrant holds an exclusive per-process file lock on its storage dir,
# so there can be only ONE client per process. Building a store per request and
# relying on GC to release the lock is fragile: a request that errors mid-flight
# (e.g. the generator raising) keeps the client alive via the exception
# traceback, never releases the lock, and wedges every later request with
# "already accessed by another instance". Memoize instead — one long-lived store
# per distinct backend config, reused across requests.
_VECTOR_STORE_CACHE: dict[tuple[str, str, str], VectorStore] = {}
# A graph driver owns a connection pool: one per database per process.
_GRAPH_STORE_CACHE: dict[tuple[str, str, str], GraphStore] = {}


def register_chunker(name: str):
    def decorate(builder: Callable[[Settings], Chunker]):
        _CHUNKERS[name] = builder
        return builder

    return decorate


def register_embedder(name: str):
    def decorate(builder: Callable[[Settings], Embedder]):
        _EMBEDDERS[name] = builder
        return builder

    return decorate


def register_vector_store(name: str):
    def decorate(builder: Callable[[Settings], VectorStore]):
        _VECTOR_STORES[name] = builder
        return builder

    return decorate


def register_sparse_retriever(name: str):
    def decorate(builder: Callable[[Settings], SparseRetriever]):
        _SPARSE_RETRIEVERS[name] = builder
        return builder

    return decorate


def register_reranker(name: str):
    def decorate(builder: Callable[[Settings], Reranker]):
        _RERANKERS[name] = builder
        return builder

    return decorate


def register_generator(name: str):
    def decorate(builder: Callable[[Settings], Generator]):
        _GENERATORS[name] = builder
        return builder

    return decorate


def register_strategy(name: str):
    def decorate(builder: Callable[[Settings], RetrievalStrategy]):
        _STRATEGIES[name] = builder
        return builder

    return decorate


def register_graph_store(name: str):
    def decorate(builder: Callable[[Settings], GraphStore]):
        _GRAPH_STORES[name] = builder
        return builder

    return decorate


def make_chunker(settings: Settings) -> Chunker:
    _load_adapters()
    return _build("chunker", _CHUNKERS, settings.chunker, settings)


def make_embedder(settings: Settings) -> Embedder:
    _load_adapters()
    return _build("embedder", _EMBEDDERS, settings.embedder, settings)


def make_vector_store(settings: Settings) -> VectorStore:
    _load_adapters()
    key = (settings.vector_store, settings.qdrant_url or settings.qdrant_path, settings.collection)
    store = _VECTOR_STORE_CACHE.get(key)
    if store is None:
        store = _build("vector store", _VECTOR_STORES, settings.vector_store, settings)
        _VECTOR_STORE_CACHE[key] = store
    return store


def reset_vector_store_cache() -> None:
    """Drop cached stores (releasing their clients). For tests / a clean rebuild."""
    _VECTOR_STORE_CACHE.clear()


def make_sparse_retriever(settings: Settings) -> SparseRetriever:
    _load_adapters()
    return _build("sparse retriever", _SPARSE_RETRIEVERS, settings.sparse_retriever, settings)


def make_reranker(settings: Settings) -> Reranker:
    _load_adapters()
    return _build("reranker", _RERANKERS, settings.reranker, settings)


def make_generator(settings: Settings) -> Generator:
    _load_adapters()
    return _build("generator", _GENERATORS, settings.generator, settings)


def make_chat_model(settings: Settings) -> ChatModel:
    """A free-form chat model from the generator registry, for strategies that call an LLM."""
    _load_adapters()
    model = _build("generator", _GENERATORS, settings.generator, settings)
    if not isinstance(model, ChatModel):
        raise TypeError(f"generator '{settings.generator}' cannot serve free-form chat completions")
    return model


def make_strategy(settings: Settings) -> RetrievalStrategy:
    _load_adapters()
    return _build("strategy", _STRATEGIES, settings.strategy, settings)


def make_graph_store(settings: Settings) -> GraphStore:
    _load_adapters()
    key = (settings.graph_store, settings.neo4j_uri, settings.neo4j_database)
    store = _GRAPH_STORE_CACHE.get(key)
    if store is None:
        store = _build("graph store", _GRAPH_STORES, settings.graph_store, settings)
        _GRAPH_STORE_CACHE[key] = store
    return store


def _build(kind: str, registry: dict, name: str, settings: Settings):
    try:
        builder = registry[name]
    except KeyError:
        available = ", ".join(sorted(registry)) or "none registered"
        raise ValueError(f"Unknown {kind} '{name}'. Available: {available}") from None
    return builder(settings)


def _load_adapters() -> None:
    # Importing the package runs every adapter module's register_* decorators.
    import sage.adapters  # noqa: F401
