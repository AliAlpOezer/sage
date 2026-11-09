"""Runtime configuration. One frozen Settings object, read from .env / environment.

The component names (embedder, vector_store, generator) are the factory keys —
change them here or in .env to swap backends.
"""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from dotenv import load_dotenv

# OmniRoute is a local, OpenAI-compatible gateway (`omniroute serve --daemon`) that
# pools several providers' free endpoints behind one endpoint with its own
# auto-fallback, and needs no API key. It is the default for every chat call here
# because OpenRouter's free tier is capped at ~8 req/min per key and had been 429ing
# whole eval runs. Only the *virtual* `auto/*` combo routes resolve — every explicitly
# named upstream in its catalog 401s — and only the `:free`-constrained ones are used,
# so nothing can silently select a paid `aug/*`/`tllm/*` proxy route.
OMNIROUTE_BASE_URL = "http://127.0.0.1:20128/v1"

# OmniRoute's free combo routes take no auth, but OpenAI-compatible clients still
# insist on a non-empty key, so send a placeholder.
OMNIROUTE_API_KEY = "not-needed"

# Per-provider default model, used when the model setting is left empty.
GENERATOR_DEFAULT_MODELS = {
    "omniroute": "auto/best-free",
    "openrouter": "nvidia/nemotron-3.5-super-vl:free",  # old default 404s; verified 2026-11-09
}
JUDGE_DEFAULT_MODELS = {
    "omniroute": "auto/best-free",
    "openrouter": "nvidia/nemotron-3.5-super-vl:free",  # old default 404s; verified 2026-11-09
    "groq": "llama-3.3-70b-versatile",
    # No default for gemini: its free model ids rotate, so set SAGE_JUDGE_MODEL.
}


_OPENROUTER_KEY_NAME = re.compile(r"OPENROUTER_API_KEY_(\d+)")


def read_openrouter_keys(environ: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    """(env name, key) for every non-empty OPENROUTER_API_KEY_<n>, ordered by n.

    The number is the rotation order (see `sage.openrouter`): a 429 on key n moves
    to the next number, and the highest wraps back to the lowest.
    """
    numbered = sorted(
        (int(match[1]), name)
        for name, value in environ.items()
        if (match := _OPENROUTER_KEY_NAME.fullmatch(name)) and value.strip()
    )
    return tuple((name, environ[name].strip()) for _, name in numbered)


def _default_model(table: dict[str, str], provider: str, env_name: str) -> str:
    try:
        return table[provider]
    except KeyError:
        raise RuntimeError(
            f"no default model for provider {provider!r} — set {env_name} explicitly."
        ) from None


@dataclass(frozen=True)
class Settings:
    # (env name, key) pairs from OPENROUTER_API_KEY_1..N, rotated on 429 by sage.openrouter.
    openrouter_api_keys: tuple[tuple[str, str], ...] = field(default=(), repr=False)
    chunker: str = "recursive"
    chunk_max_chars: int = 1800
    chunk_overlap_chars: int = 200
    # Day-38 contextual retrieval. `chunker=structural|contextual` wraps this base
    # chunker and prepends a situating prefix before embedding; both change chunk
    # ids, so both need their own `collection`.
    contextual_base_chunker: str = "recursive"
    contextual_blurb_cache: str = "data/page_blurbs.json"
    contextual_blurb_max_tokens: int = 2000  # reasoning models think before the sentence
    embedder: str = "openrouter"
    embedding_model: str = "openai/text-embedding-3-small"
    embed_batch_size: int = 128
    embed_concurrency: int = 8
    fetch_concurrency: int = 8
    vector_store: str = "qdrant"
    qdrant_path: str = "data/qdrant"
    collection: str = "langchain-docs"
    assembly_order: str = "edges"  # edges | naive (Day-33 Lost-in-the-Middle knob)
    sparse_retriever: str = "none"  # none | bm25 (Day-36 hybrid search). "none" = dense-only baseline.
    reranker: str = "none"  # none | bge | cohere (Day-37 precision stage). "none" = passthrough baseline.
    retrieve_k: int = 30  # width of the first-stage candidate set when a reranker is active
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v3.5"
    omniroute_base_url: str = OMNIROUTE_BASE_URL
    generator: str = "omniroute"
    generation_model: str = ""  # "" = GENERATOR_DEFAULT_MODELS[generator]
    # Reasoning models spend this ceiling on thinking before the answer starts, so a
    # tight cap comes back as an empty completion rather than a short one.
    generation_max_tokens: int = 4000
    judge_provider: str = "omniroute"  # omniroute | openrouter | groq | gemini
    judge_model: str = ""  # "" = JUDGE_DEFAULT_MODELS[judge_provider]
    judge_max_tokens: int = 4000
    groq_api_key: str = ""
    groq_api_keys: tuple[str, ...] = ()  # extra keys from separate orgs, splits judge load
    gemini_api_key: str = ""
    docs_index_url: str = "https://docs.langchain.com/sitemap.xml"
    docs_url_prefix: str = "https://docs.langchain.com/oss/python/"
    top_k: int = 5

    @property
    def resolved_generation_model(self) -> str:
        """The generation model actually sent, after per-provider defaulting."""
        return self.generation_model or _default_model(
            GENERATOR_DEFAULT_MODELS, self.generator, "SAGE_GENERATION_MODEL"
        )

    @property
    def resolved_judge_model(self) -> str:
        """The judge model actually sent, after per-provider defaulting."""
        return self.judge_model or _default_model(
            JUDGE_DEFAULT_MODELS, self.judge_provider, "SAGE_JUDGE_MODEL"
        )

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        d = cls()
        return cls(
            openrouter_api_keys=read_openrouter_keys(os.environ),
            chunker=os.getenv("SAGE_CHUNKER", d.chunker),
            chunk_max_chars=int(os.getenv("SAGE_CHUNK_MAX_CHARS", str(d.chunk_max_chars))),
            chunk_overlap_chars=int(os.getenv("SAGE_CHUNK_OVERLAP_CHARS", str(d.chunk_overlap_chars))),
            contextual_base_chunker=os.getenv(
                "SAGE_CONTEXTUAL_BASE_CHUNKER", d.contextual_base_chunker
            ),
            contextual_blurb_cache=os.getenv("SAGE_CONTEXTUAL_BLURB_CACHE", d.contextual_blurb_cache),
            contextual_blurb_max_tokens=int(
                os.getenv("SAGE_CONTEXTUAL_BLURB_MAX_TOKENS", str(d.contextual_blurb_max_tokens))
            ),
            embedder=os.getenv("SAGE_EMBEDDER", d.embedder),
            embedding_model=os.getenv("SAGE_EMBEDDING_MODEL", d.embedding_model),
            embed_batch_size=int(os.getenv("SAGE_EMBED_BATCH_SIZE", str(d.embed_batch_size))),
            embed_concurrency=int(os.getenv("SAGE_EMBED_CONCURRENCY", str(d.embed_concurrency))),
            fetch_concurrency=int(os.getenv("SAGE_FETCH_CONCURRENCY", str(d.fetch_concurrency))),
            vector_store=os.getenv("SAGE_VECTOR_STORE", d.vector_store),
            qdrant_path=os.getenv("SAGE_QDRANT_PATH", d.qdrant_path),
            collection=os.getenv("SAGE_COLLECTION", d.collection),
            assembly_order=os.getenv("SAGE_ASSEMBLY_ORDER", d.assembly_order),
            sparse_retriever=os.getenv("SAGE_SPARSE_RETRIEVER", d.sparse_retriever),
            reranker=os.getenv("SAGE_RERANKER", d.reranker),
            retrieve_k=int(os.getenv("SAGE_RETRIEVE_K", str(d.retrieve_k))),
            cohere_api_key=os.getenv("COHERE_API_KEY", d.cohere_api_key),
            cohere_rerank_model=os.getenv("SAGE_COHERE_RERANK_MODEL", d.cohere_rerank_model),
            omniroute_base_url=os.getenv("SAGE_OMNIROUTE_BASE_URL", d.omniroute_base_url),
            generator=os.getenv("SAGE_GENERATOR", d.generator),
            generation_model=os.getenv("SAGE_GENERATION_MODEL", d.generation_model),
            generation_max_tokens=int(
                os.getenv("SAGE_GENERATION_MAX_TOKENS", str(d.generation_max_tokens))
            ),
            judge_provider=os.getenv("SAGE_JUDGE_PROVIDER", d.judge_provider),
            judge_model=os.getenv("SAGE_JUDGE_MODEL", d.judge_model),
            judge_max_tokens=int(os.getenv("SAGE_JUDGE_MAX_TOKENS", str(d.judge_max_tokens))),
            groq_api_key=os.getenv("GROQ_API_KEY", d.groq_api_key),
            groq_api_keys=tuple(
                k.strip() for k in os.getenv("GROQ_API_KEYS", "").split(",") if k.strip()
            ),
            gemini_api_key=os.getenv("GEMINI_API_KEY", d.gemini_api_key),
            docs_index_url=os.getenv("SAGE_DOCS_INDEX_URL", d.docs_index_url),
            docs_url_prefix=os.getenv("SAGE_DOCS_URL_PREFIX", d.docs_url_prefix),
            top_k=int(os.getenv("SAGE_TOP_K", str(d.top_k))),
        )
