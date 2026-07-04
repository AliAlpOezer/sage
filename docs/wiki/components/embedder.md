---
type: component
title: Embedder (port) — OpenRouterEmbedder
description: Async batched embedding client against OpenRouter's OpenAI-compatible endpoint.
resource: src/sage/adapters/openrouter_embedder.py
tags: [embeddings, port, async]
timestamp: 2026-07-04T00:00:00Z
---

Port: `async Embedder.embed(texts) -> list[list[float]]`, result order matches
input. Selected by `SAGE_EMBEDDER` (default `openrouter`); model by
`SAGE_EMBEDDING_MODEL` (default `openai/text-embedding-3-small`, 1536 dims).

Mechanics worth reading (this file is the asyncio bounded-concurrency drill in
miniature): batches of `SAGE_EMBED_BATCH_SIZE=128`; `asyncio.Semaphore(SAGE_EMBED_CONCURRENCY=8)`
around `asyncio.gather`; retry with exponential backoff on 429/500/502/503;
results sorted by the API's `index` field, never trusted by position.

- The port deliberately has NO `dimension` property — ingest derives dims from
  `len(vectors[0])`, so new models need no dimension table entry.
- Planned adapter #2: local sentence-transformers.
  Decision & alternatives: [embedding-strategy](../decisions/embedding-strategy.md).
