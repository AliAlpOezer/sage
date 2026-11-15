"""Backend implementations.

Importing this package registers every adapter with the factory. Add new
adapter modules to the imports below.
"""

from sage.adapters import (  # noqa: F401
    bm25_store,
    chat_generator,
    chunkers,
    contextual,
    openrouter_embedder,
    qdrant_store,
    rerank,
    vector_strategy,
)
