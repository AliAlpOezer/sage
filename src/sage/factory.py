"""Config-keyed factories for the swappable components.

Each port has a registry mapping a short name (what goes in .env) to a builder.
Adapters register themselves at import time via the register_* decorators, so
adding a backend is: write the adapter, decorate it, set its name in .env.
"""

from collections.abc import Callable

from sage.config import Settings
from sage.ports import Chunker, Embedder, Generator, VectorStore

_CHUNKERS: dict[str, Callable[[Settings], Chunker]] = {}
_EMBEDDERS: dict[str, Callable[[Settings], Embedder]] = {}
_VECTOR_STORES: dict[str, Callable[[Settings], VectorStore]] = {}
_GENERATORS: dict[str, Callable[[Settings], Generator]] = {}


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


def register_generator(name: str):
    def decorate(builder: Callable[[Settings], Generator]):
        _GENERATORS[name] = builder
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
    return _build("vector store", _VECTOR_STORES, settings.vector_store, settings)


def make_generator(settings: Settings) -> Generator:
    _load_adapters()
    return _build("generator", _GENERATORS, settings.generator, settings)


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
