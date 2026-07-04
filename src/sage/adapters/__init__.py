"""Backend implementations.

Importing this package registers every adapter with the factory. Add new
adapter modules to the imports below.
"""

from sage.adapters import (  # noqa: F401
    chunkers,
    openrouter_embedder,
    openrouter_generator,
    qdrant_store,
)
