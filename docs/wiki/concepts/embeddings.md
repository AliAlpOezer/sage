---
type: concept
title: What is an embedding
description: Text mapped to a point in high-dimensional space so that similar meanings land close together.
tags: [embeddings, fundamentals]
timestamp: 2026-07-04T00:00:00Z
---

An **embedding** is text converted into a list of numbers — here, 1536 of them
— that places the text as a point in a high-dimensional space. The model that
produces them is trained (by contrastive learning over huge pair datasets) so
that *texts with similar meaning land near each other*: "persist conversation
history" lands close to "memory", despite sharing zero words. That single
property turns search into geometry: embed the question, find the nearest
stored points, and you have semantic lookup without keywords.

Facts that matter in practice:

- **A vector summarizes everything in its text.** Long, multi-topic text →
  a muddy average that matches nothing strongly. This is half the reason
  [chunking](../decisions/chunking-strategy.md) exists.
- **Vectors are only comparable within one model.** Different models (even
  versions) produce unrelated coordinate systems. Corpus and queries must use
  the same embedder — in this codebase that is one config value, by design.
- **Dimension count** (1536 for text-embedding-3-small, 3072 for -large) is
  fixed per model. More dims ≈ more capacity, more storage, marginal quality.
- **Dense vs sparse:** dense embeddings capture meaning but smear rare exact
  tokens (identifiers, error strings) — the classic weakness that keyword
  methods (BM25) don't have, and why hybrids exist
  ([details](../decisions/embedding-strategy.md)).
- **"Closeness"** is measured with cosine similarity here
  ([why](../decisions/similarity-metric.md)).
