"""Backend implementations.

Importing this package registers every adapter with the factory. Add new
adapter modules to the imports below.
"""

from sage.adapters import chunkers, openrouter_embedder, qdrant_store  # noqa: F401
