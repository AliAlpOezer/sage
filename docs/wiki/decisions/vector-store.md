---
type: decision
title: Vector store — Qdrant embedded local mode first, pgvector second
description: Zero-infrastructure file-backed Qdrant for the first loop; pgvector planned as adapter #2 to prove the port.
resource: src/sage/adapters/qdrant_store.py
tags: [vector-search, infrastructure]
timestamp: 2026-07-04T00:00:00Z
---

## Context
Where do 4820 vectors live, and what algorithm finds the nearest ones? Docker
is installed (29.6.1) but its daemon is usually stopped on this machine —
relevant because pgvector needs a running Postgres.

## What we chose
**Qdrant in embedded local mode**: runs inside the Python process
(`QdrantClient(path="data/qdrant")`), persists to disk, zero infrastructure.
First loop working the same day. **pgvector is the committed adapter #2**
(user preference + proves the VectorStore port abstraction).

## How it works — the search algorithm
At this scale Qdrant local mode does **exact brute-force search**: the query
vector is compared against all 4820 stored vectors (~7M multiplications —
milliseconds in numpy) and the true top-k wins. The famous **ANN** (approximate
nearest neighbor) algorithms — chiefly **HNSW**, a multi-layer graph of
shortcuts you descend greedily, log-ish search time at ~99% recall instead of
100% — exist because brute force dies at *millions* of vectors. Server Qdrant
builds HNSW; at 4820 vectors it isn't needed, and knowing when you don't need
it is part of the lesson.

## Alternatives & trade-offs
- **pgvector** (Postgres extension; vectors as a column type) — vectors live
  next to relational data, SQL joins with app tables, one boring proven
  database to operate. Needs Docker/Postgres running. Scheduled as Bucket 5
  precisely to demonstrate the swap.
- **FAISS** — a raw similarity-search library, extremely fast; but no
  persistence/filtering/serving layer — you build the database parts yourself.
- **Chroma** — same embedded-local niche as Qdrant local mode; comparable.
- **Managed SaaS (Pinecone etc.)** — zero ops, vendor lock-in, overkill for
  4820 vectors.

## Why this serves the goal
Fastest path to end-to-end on Day 25, while the port keeps the pgvector
comparison one env line away.

## Revisit when
Bucket 5 (pgvector adapter), or corpus growth toward ~1M vectors (then HNSW
and a served Qdrant/pgvector-with-index matter).
