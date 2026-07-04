# Sage (RAG over LangChain docs) — Context Pack
Updated: 2026-07-04

## Goal & Core Decision
Learning-first RAG over docs.langchain.com, built from scratch in Python behind
swappable ports (Embedder, VectorStore, Generator) so approaches can be compared
head-to-head. Done-when (Day 25): 10 real questions answered end-to-end, failures logged.

## Requirements
- [must] Ports + config-keyed factory; swap backends via .env only
- [must] Idempotent ingestion (chunk id = content hash → re-run gives same vector count)
- [must] Query loop: embed → top-k → context assembly → answer with source URLs
- [must] Adapter set #1: OpenRouter embeddings + Qdrant local mode + OpenRouter generation
- [should] Async embedding with bounded concurrency (semaphore)
- [should] pgvector as adapter #2 proving the abstraction
- [could] Local sentence-transformers embedder as adapter #3
## Non-goals
- Reranking, query transforms, measured evals (W5–6), UI (Day 26+), LangChain-the-framework

## Decisions (with rationale)
- From scratch, no RAG framework — user is building the abstractions to learn them. (2026-07-04)
- httpx over OpenAI SDK for OpenRouter — see raw request/response shapes. (2026-07-04)
- OpenRouter one key for embeddings AND generation — OpenRouter now has an
  OpenAI-compatible /api/v1/embeddings endpoint. (2026-07-04)
- Qdrant first via qdrant-client local mode (no Docker needed), pgvector second.
  Docker installed (29.6.1) but daemon usually stopped. (2026-07-04)
- Corpus index: sitemap.xml, NOT /llms.txt — llms.txt hard-truncates at 100K chars
  and omits the entire /oss/ section. Sitemap has 1418 URLs; append .md for markdown. (2026-07-04)
- Scope: /oss/python/ (185 pages, ~1.2M tokens ≈ $0.025 to embed) — the LangChain 1.0
  Python docs the sprint targets; excludes the JS mirror. Configurable. (2026-07-04)
- Chunker is a fourth port with its own registry — W5 measures chunking strategies
  head-to-head, same swap mechanism as the other backends. (2026-07-04)
- Embedder port has no dimension property — ingest derives dims from len(vectors[0]);
  no per-model dimension table to maintain. (2026-07-04)
- Chunk ids: sha256(source_url + text) formatted as UUID — Qdrant only accepts
  UUID/int point ids; deterministic id gives idempotent upserts. (2026-07-04)
- Embedding model: openai/text-embedding-3-small (1536 dims, cosine). Generation:
  anthropic/claude-sonnet-4-6. Both are .env values. (2026-07-04)

## Current State
- Done: Bucket 1 — repo skeleton, ports, factory, Settings, tests.
- Done: Bucket 2 scaffold — loader (sitemap → 185 md pages, verified live),
  OpenRouter embedder (batched, semaphore-bounded, retry on 429/5xx),
  Qdrant local-mode store, ingest pipeline, chunker executable spec
  (tests/test_chunker.py — 8 tests, skip until implemented).
- BLOCKED ON USER (by design): implement RecursiveChunker.chunk() in
  src/sage/adapters/chunkers.py — sprint protocol, hand-written.
  Then: `uv run python -m pytest` green → `uv run python -m sage.ingest`.
- Then: Bucket 3 query loop (`ask.py`), Bucket 4 ten-question failure log,
  Bucket 5 pgvector adapter.

## Open Questions
- Exact /oss/ page count and token volume (measure during Bucket 2).
- pgvector schema (Bucket 5): single table, vector column dims fixed per embedder.

## Key Files / Interfaces
- `src/sage/ports.py` — Chunker (chunk(Page) -> list[Chunk]), Embedder (async embed),
  VectorStore (ensure_collection/upsert/search/count), Generator (generate)
- `src/sage/loader.py` — sitemap parse + concurrent page fetch -> list[Page]
- `src/sage/ingest.py` — load → chunk → embed → upsert (run: python -m sage.ingest)
- `src/sage/factory.py` — register_* decorators + make_* builders keyed by Settings
- `src/sage/config.py` — frozen Settings dataclass, Settings.from_env()
- `src/sage/models.py` — Chunk (with make_id), ScoredChunk
- `src/sage/adapters/` — one module per backend, self-registering
