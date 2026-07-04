---
type: state
title: Current state — Day 25, ingestion complete
description: Ingestion pipeline built and verified end-to-end; query loop is next.
resource: docs/context/sage.md
tags: [status]
timestamp: 2026-07-04T00:00:00Z
---

## Works now (all numbers verified 2026-07-04)
- Full ingestion: `uv run python -m sage.ingest` →
  **185 pages → 4836 chunks → 4820 vectors** (1536 dims, cosine, Qdrant local).
- Idempotency proven: two consecutive runs, identical counts.
  (4836→4820 = 16 within-page duplicate texts collapsing via
  [content-hash ids](../decisions/chunk-identity.md).)
- Test suite: **11 passed** (3 factory/model + 8 chunker spec).
- Embedding cost per full ingest: ~1.2M tokens ≈ **$0.025**.

## Bucket ledger
| # | Bucket | Status |
|---|--------|--------|
| 1 | Skeleton — ports, factory, config | done (commit d95b070) |
| 2 | Ingestion — loader, embedder, store, pipeline | done (5190da1) |
| — | Hand-written chunker | done, user-authored (e889968) |
| 3 | Query loop — Generator adapter + ask.py | **next** |
| 4 | 10-question failure log (sprint done-when) | pending |
| 5 | pgvector adapter (proves the VectorStore port) | pending |

## Open questions
- Failure-log taxonomy for Bucket 4 (retrieval miss vs generation miss vs
  chunking artifact) — decide when first failures appear.
- pgvector schema (Bucket 5): single table, dims fixed per embedder.

## Operational notes
- Run tests as `uv run python -m pytest` (`pytest.exe` spawn is blocked on
  this machine). `uv` lives at `~\.local\bin\uv.exe`.
- Qdrant local mode file-locks `data/qdrant/` — one process at a time.
- Tight operational handoff (for resuming work): [context pack](../../context/sage.md).
