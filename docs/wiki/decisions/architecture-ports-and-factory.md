---
type: decision
title: Architecture — from scratch, ports & adapters, config-keyed factory
description: Build the RAG pipeline without a framework; every stage behind a swappable Protocol, selected by name from .env.
resource: src/sage/factory.py
tags: [architecture, learning]
timestamp: 2026-07-04T00:00:00Z
---

## Context
First decision of the project: build on a RAG framework or from scratch, and
how to structure the code so different approaches (embedders, stores, chunkers)
can be compared head-to-head.

## What we chose
From scratch — direct SDKs only (httpx, qdrant-client). Four **ports**
(interfaces, as Python `Protocol`s): [Chunker](../components/chunker.md),
[Embedder](../components/embedder.md), [VectorStore](../components/vector-store.md),
[Generator](../components/generator.md). A **factory** holds one registry per
port; adapters self-register at import time via `@register_*("name")`
decorators, and `.env` values (`SAGE_EMBEDDER=openrouter`, …) select which
adapter gets built. Swapping a backend = one env line, zero code changes.

## How it works
A port says *what* a stage must do (`embed(texts) -> vectors`); an adapter is
one concrete way of doing it (call OpenRouter). The factory is the lookup that
turns the config string into a constructed adapter. This is the classic
"ports & adapters" (hexagonal) pattern plus a registry-based factory.

## Alternatives & trade-offs
- **LangChain / LlamaIndex** — batteries included (loaders, splitters, store
  wrappers), fastest to a demo. But their abstractions ARE the thing being
  learned here; using them would outsource exactly the design experience the
  project exists to build. Also fitting-but-circular: the corpus is LangChain's
  own docs.
- **Hybrid** (own ports, framework utilities inside adapters) — legitimate
  middle ground; rejected for now to keep every mechanism visible.
- **No abstraction, single hardcoded pipeline** — least code today, but the
  W5 sprint measures strategies against each other; without ports that becomes
  copy-paste forks.

## Why this serves the goal
The project goal is learning-first with comparable approaches; the ports are
the comparison harness.

## Revisit when
If adapter count grows past ~3 per port and maintenance drags, consider
borrowing framework components inside adapters (the ports hide them anyway).
