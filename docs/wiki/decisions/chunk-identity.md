---
type: decision
title: Chunk identity — content-hash ids (sha256 → UUID)
description: Deterministic ids make ingestion idempotent; re-runs overwrite instead of duplicate.
resource: src/sage/models.py
tags: [ingestion, idempotency]
timestamp: 2026-07-04T00:00:00Z
---

## Context
Every chunk needs an id for upserting. Ingestion will be re-run constantly
while iterating on chunking; duplicates silently corrupt every retrieval
measurement afterward.

## What we chose
`id = sha256(source_url + "\n" + text)`, formatted as a UUID because Qdrant
only accepts UUIDs or unsigned ints as point ids. Same content → same id →
**upsert overwrites instead of duplicating**.

## Verified behavior (2026-07-04)
Two consecutive `python -m sage.ingest` runs: identical counts both times —
idempotency proven. Also observed: **4836 chunks → 4820 vectors**. Sixteen
chunks have identical (url, text) — repeated boilerplate snippets within a
page — so they collapse to the same point. Dedupe as a side effect of hash
identity, visible in the numbers.

## Alternatives & trade-offs
- **Random UUIDs / auto-increment** — every re-run doubles the store;
  idempotency would need explicit delete-before-insert bookkeeping.
- **URL + position as id** — stable across runs only until the chunker
  changes; editing one paragraph shifts every subsequent position and orphans
  stale points. Content hashing localizes change.
- Trade-off accepted: identical texts collapse (usually desirable), and stale
  chunks from *deleted* source content linger until a cleanup pass (a re-index
  from scratch clears them — cheap at $0.025).

## Why this serves the goal
Day 24's acceptance criterion ("run ingest twice → identical vector count")
falls out of the design instead of being bolted on.

## Revisit when
Incremental sync matters (delete-detection needs a manifest of live ids per
page).
