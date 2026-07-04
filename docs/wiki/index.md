# sage — knowledge bundle index

RAG over the LangChain docs, built from scratch as a learning project.
Start here; every page is one concept. Maintained by the `/document` skill.

## State
- [current-state](state/current-state.md) — Day 25: ingestion verified end-to-end (185 pages → 4820 vectors); query loop next.

## Decisions (each: what we chose, how it works, alternatives & trade-offs)
- [architecture-ports-and-factory](decisions/architecture-ports-and-factory.md) — from scratch, four Protocol ports, registry factory keyed by .env.
- [corpus-source](decisions/corpus-source.md) — sitemap.xml + per-page .md; llms.txt rejected (truncated at 100K chars).
- [corpus-scope](decisions/corpus-scope.md) — /oss/python/ only (185 of 1418 pages); retrieval-noise rationale.
- [chunking-strategy](decisions/chunking-strategy.md) — hand-written recursive splitter; vs fixed-window, semantic, whole-page; size/overlap trade-offs.
- [embedding-strategy](decisions/embedding-strategy.md) — dense text-embedding-3-small via OpenRouter; vs BM25/hybrid, -large, local models; call mechanics.
- [similarity-metric](decisions/similarity-metric.md) — cosine; why dot/Euclidean are equivalent here and cosine is the safe default.
- [vector-store](decisions/vector-store.md) — Qdrant embedded local (exact search) first, pgvector second; vs FAISS/Chroma/SaaS; when HNSW matters.
- [chunk-identity](decisions/chunk-identity.md) — content-hash ids → idempotent ingestion; explains the 4836→4820 collapse.
- [generation-model](decisions/generation-model.md) — claude-sonnet-4-6, top_k=5; Haiku-class comparison and lost-in-the-middle pending.

## Components (the moving parts)
- [loader](components/loader.md) — sitemap → concurrent markdown fetch → Page objects.
- [chunker](components/chunker.md) — Chunker port; user-authored RecursiveChunker + its executable spec.
- [embedder](components/embedder.md) — Embedder port; batched, semaphore-bounded OpenRouter client.
- [vector-store](components/vector-store.md) — VectorStore port; Qdrant local-mode adapter.
- [generator](components/generator.md) — Generator port; NOT yet implemented (Bucket 3).

## Concepts (beginner-first explainers)
- [rag-pipeline](concepts/rag-pipeline.md) — the two data flows, why each stage exists, what "naive" deliberately leaves out (the W5–6 map).
- [embeddings](concepts/embeddings.md) — what an embedding is; the same-model rule; dense vs sparse.
