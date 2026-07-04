---
type: decision
title: Corpus scope — /oss/python/ only (185 pages)
description: Index only the LangChain OSS Python docs, not all 1418 site pages.
resource: src/sage/config.py
tags: [ingestion, corpus, retrieval-quality]
timestamp: 2026-07-04T00:00:00Z
---

## Context
The sitemap lists 1418 URLs: 997 LangSmith, 376 OSS (Python + JavaScript
mirrors), 43 API reference. What belongs in the store?

## What we chose
`SAGE_DOCS_URL_PREFIX=https://docs.langchain.com/oss/python/` → **185 pages,
4.86M chars ≈ 1.2M tokens** (measured 2026-07-04).

## How it works
Retrieval returns the top-k *nearest* chunks — nearest among everything in the
store. Every off-topic page embedded is a candidate that can outrank a relevant
one. Ask "how does create_agent work?" against a store that also holds 900
LangSmith admin pages and some of them may score deceptively well, crowding the
top-5. A smaller on-topic corpus keeps the vector neighborhoods clean.

## Alternatives & trade-offs
- **Whole site (1418 pages)** — broader coverage (LangSmith questions become
  answerable) at the cost of retrieval noise on the core use case, ~8x embedding
  volume, and mixed-language (Python/JS) near-duplicates that split scores
  across twins.
- **/oss/ (Python + JS, 376 pages)** — JS mirror pages are near-duplicates of
  the Python ones; they dilute top-k with same-content-different-language hits.
- **Hand-picked page list** — maximal control, doesn't survive docs reorgs.

## Why this serves the goal
The sprint targets "the LangChain 1.0 (Python) docs"; scope matches the
questions the 10-question eval will ask.

## Revisit when
The failure log shows questions that need LangSmith or JS pages — widen the
prefix (it's one env var) and re-ingest (~cents).
