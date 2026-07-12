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
    chunker: str = "recursive"
    chunk_max_chars: int = 1800
    chunk_overlap_chars: int = 200
    embedder: str = "openrouter"
    embedding_model: str = "openai/text-embedding-3-small"
    embed_batch_size: int = 128
    embed_concurrency: int = 8
    fetch_concurrency: int = 8
    vector_store: str = "qdrant"
    qdrant_path: str = "data/qdrant"
    collection: str = "langchain-docs"
    assembly_order: str = "edges"  # edges | naive (Day-33 Lost-in-the-Middle knob)
    generator: str = "openrouter"
    generation_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    judge_provider: str = "openrouter"  # openrouter | groq | gemini
    judge_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    docs_index_url: str = "https://docs.langchain.com/sitemap.xml"
    docs_url_prefix: str = "https://docs.langchain.com/oss/python/"
    top_k: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        d = cls()
        return cls(
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", d.openrouter_api_key),
            chunker=os.getenv("SAGE_CHUNKER", d.chunker),
            chunk_max_chars=int(os.getenv("SAGE_CHUNK_MAX_CHARS", str(d.chunk_max_chars))),
            chunk_overlap_chars=int(os.getenv("SAGE_CHUNK_OVERLAP_CHARS", str(d.chunk_overlap_chars))),
            embedder=os.getenv("SAGE_EMBEDDER", d.embedder),
            embedding_model=os.getenv("SAGE_EMBEDDING_MODEL", d.embedding_model),
            embed_batch_size=int(os.getenv("SAGE_EMBED_BATCH_SIZE", str(d.embed_batch_size))),
            embed_concurrency=int(os.getenv("SAGE_EMBED_CONCURRENCY", str(d.embed_concurrency))),
            fetch_concurrency=int(os.getenv("SAGE_FETCH_CONCURRENCY", str(d.fetch_concurrency))),
            vector_store=os.getenv("SAGE_VECTOR_STORE", d.vector_store),
            qdrant_path=os.getenv("SAGE_QDRANT_PATH", d.qdrant_path),
            collection=os.getenv("SAGE_COLLECTION", d.collection),
            assembly_order=os.getenv("SAGE_ASSEMBLY_ORDER", d.assembly_order),
            generator=os.getenv("SAGE_GENERATOR", d.generator),
            generation_model=os.getenv("SAGE_GENERATION_MODEL", d.generation_model),
            judge_provider=os.getenv("SAGE_JUDGE_PROVIDER", d.judge_provider),
            judge_model=os.getenv("SAGE_JUDGE_MODEL", d.judge_model),
            groq_api_key=os.getenv("GROQ_API_KEY", d.groq_api_key),
            gemini_api_key=os.getenv("GEMINI_API_KEY", d.gemini_api_key),
            docs_index_url=os.getenv("SAGE_DOCS_INDEX_URL", d.docs_index_url),
            docs_url_prefix=os.getenv("SAGE_DOCS_URL_PREFIX", d.docs_url_prefix),
            top_k=int(os.getenv("SAGE_TOP_K", str(d.top_k))),
        )
