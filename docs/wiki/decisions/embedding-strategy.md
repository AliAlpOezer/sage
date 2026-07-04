---
type: decision
title: Embedding — dense API vectors (text-embedding-3-small via OpenRouter)
description: Dense semantic embeddings, 1536 dims, one key for embeddings and generation; batched + semaphore-bounded async calls.
resource: src/sage/adapters/openrouter_embedder.py
tags: [embeddings, retrieval, cost]
timestamp: 2026-07-04T00:00:00Z
---

## Context
The pipeline needs text → vector. Which family (dense vs sparse), which model,
which provider, and how to call it efficiently.

## What we chose
**Dense semantic embedding** with `openai/text-embedding-3-small` (1536
dimensions) served through **OpenRouter** — which added an OpenAI-compatible
`/api/v1/embeddings` endpoint, so the one existing key covers both embeddings
and generation. Full-corpus cost measured: ~1.2M tokens ≈ **$0.025** per
ingest at $0.02/1M.

## How it works
See [what is an embedding](../concepts/embeddings.md). "Dense" = every one of
the 1536 dimensions holds a learned aspect of meaning, so "persist conversation
history" lands near "memory" despite sharing zero words.

**The one rule that cannot be broken:** queries must be embedded by the exact
same model as the corpus. Vectors from different models live in unrelated
coordinate systems — comparing them is meaningless. This is why the embedder is
ONE config value used by both ingest and query paths.

**Call mechanics:** batches of `SAGE_EMBED_BATCH_SIZE=128` texts per request;
at most `SAGE_EMBED_CONCURRENCY=8` requests in flight via `asyncio.Semaphore`
(unbounded gather → rate-limit storms; sequential → ~8x slower); retry with
backoff on 429/5xx; results re-ordered by the API's `index` field rather than
trusting response order.

## Alternatives & trade-offs
- **Sparse / lexical (BM25)** — classic keyword search: scores exact word
  overlap weighted by rarity. Free, no API — and BETTER than dense retrieval
  for exact identifiers (`AgentExecutor`, error strings), which dense vectors
  smear. Weakness is the inverse: zero synonym generalization. Production
  answer is **hybrid** (both + merge) — the expected W5 upgrade once the
  failure log shows dense whiffing on API names.
- **text-embedding-3-large** — 3072 dims, ~6x price, a few benchmark points
  better. Diminishing returns for a docs corpus.
- **Local models (sentence-transformers: BGE, MiniLM)** — free, offline,
  private; slower on CPU, generally somewhat weaker. Planned adapter #3; the
  swap is one env line.
- **Multi-vector (ColBERT) / rerankers** — later-stage tools (W5–6), not
  first-pass retrieval.

## Why this serves the goal
Cheapest strong default that makes model comparison trivial later (OpenRouter
exposes many embedding models behind the same endpoint).

## Revisit when
Failure log shows identifier-lookup misses (→ hybrid/BM25), or the local-model
comparison lands (adapter #3).
