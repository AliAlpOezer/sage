---
type: decision
title: Similarity metric — cosine
description: Closeness between vectors is measured as the angle between them; standard for text embeddings.
resource: src/sage/adapters/qdrant_store.py
tags: [retrieval, vector-search]
timestamp: 2026-07-04T00:00:00Z
---

## Context
"Nearest" chunks needs a definition of *distance* between vectors. Set once per
collection (`Distance.COSINE` in `ensure_collection`).

## What we chose
**Cosine similarity** — the angle between two vectors, ignoring their lengths.
The convention for text embeddings.

## Alternatives & trade-offs
- **Dot product** — angle x magnitude. OpenAI embeddings come pre-normalized
  to length 1, so dot product is mathematically identical to cosine here;
  choosing it would change nothing until a non-normalized model is swapped in,
  at which point it would silently change ranking. Cosine is the safe choice.
- **Euclidean (L2) distance** — straight-line distance; also rank-equivalent
  to cosine for normalized vectors. Same story.

The honest summary: for this model the choice barely matters, and cosine is
the option that stays correct if the embedder changes.

## Why this serves the goal
One less thing that can silently break when comparing embedding adapters.

## Revisit when
An embedding model that recommends dot product (some retrieval-tuned models
do) is adapted in — the metric lives with the collection, so re-ingest.
