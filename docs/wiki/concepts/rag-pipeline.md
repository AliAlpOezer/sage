---
type: concept
title: The RAG pipeline — big picture, and what "naive" means
description: The two data flows, why each stage exists, and the known gaps this project deliberately ships with.
tags: [rag, overview]
timestamp: 2026-07-04T00:00:00Z
---

RAG (Retrieval-Augmented Generation) answers questions by **looking things up
first**: instead of trusting what the language model memorized, you retrieve
the relevant passages from your own corpus and hand them to the model as
context, so answers are grounded in (and citable to) real sources.

Two separate data flows:

```
INGESTION (run when the corpus changes):
  load docs -> chunk -> embed -> upsert to vector store
     |          |         |            |
  loader     chunker   embedder    vector store        <- the four ports

QUERY (run per question):
  embed the question -> top-k nearest chunks -> assemble context -> generate answer
     (SAME embedder!)      (vector store)       (order matters)     (generator)
```

Why each stage exists:
- **Chunking** — the context window can't hold everything, and an embedding of
  a whole page is a muddy average of many topics ([details](../decisions/chunking-strategy.md)).
- **Embedding** — turns "similar meaning" into "nearby points" so lookup
  becomes geometry ([what is an embedding](embeddings.md)).
- **Vector store** — the database that answers "which stored vectors are
  nearest to this one?" ([details](../decisions/vector-store.md)).
- **Context assembly** — top-k chunks ordered for the model; models attend
  most to the edges of the context ("lost in the middle"), so strongest
  evidence goes first/last.
- **Generation** — the model answers *from the provided context*, citing
  sources ([details](../decisions/generation-model.md)).

## What "naive" means here — the deliberate gaps

Single dense retriever, fixed top-k, no hybrid/BM25 keyword leg, no reranking,
no query rewriting, no measured evals. Every failure logged in the 10-question
eval should point at one of these gaps; they are the W5–6 upgrade map:

| Symptom in the failure log | Missing piece |
|---|---|
| Misses exact API names / error strings | Hybrid retrieval (BM25 + dense) |
| Right page retrieved, wrong passage ranked top | Reranker |
| Question phrased unlike docs vocabulary | Query rewriting / expansion |
| "It feels better" with no numbers | Eval harness (failure log becomes the test set) |
