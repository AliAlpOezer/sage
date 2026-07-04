---
type: component
title: VectorStore (port) — QdrantStore
description: Embedded local-mode Qdrant; cosine collection, id-based upsert, top-k search.
resource: src/sage/adapters/qdrant_store.py
tags: [vector-search, port]
timestamp: 2026-07-04T00:00:00Z
---

Port: `ensure_collection(dimension)` (idempotent create) · `upsert(chunks,
vectors)` (overwrite-by-id) · `search(vector, k) -> list[ScoredChunk]` ·
`count()`. Selected by `SAGE_VECTOR_STORE` (default `qdrant`).

Current adapter: **QdrantStore**, embedded local mode —
`QdrantClient(path=SAGE_QDRANT_PATH)` (default `data/qdrant`, gitignored),
collection `SAGE_COLLECTION=langchain-docs`, cosine distance. Chunk payload
(text, source_url, title, position) rides on each point and is reconstructed
into `Chunk` objects at search time.

- Local mode = exact brute-force search — correct and fast at 4820 vectors;
  see [vector-store decision](../decisions/vector-store.md) for the
  HNSW/at-scale story.
- Note: local mode holds a file lock — don't run ingest and queries in two
  processes simultaneously.
- Store state (verified 2026-07-04): 4820 vectors, dimension 1536.
- Planned adapter #2: pgvector (Bucket 5) — proves the port.
