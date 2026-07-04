---
type: decision
title: Corpus source — sitemap.xml + per-page markdown
description: Enumerate pages from sitemap.xml and fetch each as clean markdown by appending .md; llms.txt proved truncated.
resource: src/sage/loader.py
tags: [ingestion, corpus]
timestamp: 2026-07-04T00:00:00Z
---

## Context
How to get the documentation text out of docs.langchain.com and into the
pipeline, cleanly.

## What we chose
Parse `https://docs.langchain.com/sitemap.xml` for page URLs, filter by prefix,
fetch each page with `.md` appended — the docs platform (Mintlify) serves clean
markdown per page. Concurrent fetch bounded by a semaphore
(`SAGE_FETCH_CONCURRENCY=8`).

## How it works
A sitemap is the machine-readable list of every URL a site publishes. The `.md`
trick means no HTML parsing at all: what we ingest is the same markdown the
docs authors wrote.

## Alternatives & trade-offs
- **llms.txt** (the purpose-built LLM index) — tried FIRST and rejected on
  evidence: it hard-truncates at 100,000 characters and the entire `/oss/`
  section (our corpus!) is what got cut. Lesson recorded: verify the data
  source before building on it.
- **HTML crawling + parsing** (BeautifulSoup etc.) — works on any site, and is
  the honest default when no markdown endpoint exists. Cost: navigation,
  footers and scripts leak into chunks and pollute retrieval; parsing is a
  permanent maintenance surface.
- **Cloning the docs GitHub repo** — clean source, but drifts from the
  published site and contains MDX templating that isn't what readers see.

## Why this serves the goal
Cleanest possible input with the least code — more time on the retrieval
mechanics that the project is actually about.

## Revisit when
The `.md` endpoint disappears, or a corpus without such an endpoint is added
(then: HTML crawling as a second loader adapter).
