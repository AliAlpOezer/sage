"""Runtime configuration. One frozen Settings object, read from .env / environment.

The component names (embedder, vector_store, generator) are the factory keys —
change them here or in .env to swap backends.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = ""
    embedder: str = "openrouter"
    embedding_model: str = "openai/text-embedding-3-small"
    vector_store: str = "qdrant"
    qdrant_path: str = "data/qdrant"
    collection: str = "langchain-docs"
    generator: str = "openrouter"
    generation_model: str = "anthropic/claude-sonnet-4-6"
    docs_index_url: str = "https://docs.langchain.com/llms.txt"
    docs_url_prefix: str = "https://docs.langchain.com/oss/"
    top_k: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        d = cls()
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", d.openrouter_api_key),
            embedder=os.getenv("SAGE_EMBEDDER", d.embedder),
            embedding_model=os.getenv("SAGE_EMBEDDING_MODEL", d.embedding_model),
            vector_store=os.getenv("SAGE_VECTOR_STORE", d.vector_store),
            qdrant_path=os.getenv("SAGE_QDRANT_PATH", d.qdrant_path),
            collection=os.getenv("SAGE_COLLECTION", d.collection),
            generator=os.getenv("SAGE_GENERATOR", d.generator),
            generation_model=os.getenv("SAGE_GENERATION_MODEL", d.generation_model),
            docs_index_url=os.getenv("SAGE_DOCS_INDEX_URL", d.docs_index_url),
            docs_url_prefix=os.getenv("SAGE_DOCS_URL_PREFIX", d.docs_url_prefix),
            top_k=int(os.getenv("SAGE_TOP_K", str(d.top_k))),
        )
