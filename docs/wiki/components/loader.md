---
type: component
title: Loader
description: sitemap.xml -> filtered URL list -> concurrent fetch of per-page markdown -> list[Page].
resource: src/sage/loader.py
tags: [ingestion]
timestamp: 2026-07-04T00:00:00Z
---

Fetches the corpus. `parse_index()` extracts `<loc>` URLs from the sitemap,
filters by `SAGE_DOCS_URL_PREFIX`, dedupes, appends `.md`. `load_pages()`
fetches all pages concurrently (httpx.AsyncClient, `asyncio.Semaphore`
bounded by `SAGE_FETCH_CONCURRENCY=8`), skipping failures with a warning.

- Interface: `async load_pages(settings) -> list[Page]`; `Page(url, title, markdown)`.
- Title = first `# ` heading, else humanized URL slug.
- Not a registered port (single implementation so far); becomes one if a
  second corpus type arrives. Decisions: [corpus-source](../decisions/corpus-source.md),
  [corpus-scope](../decisions/corpus-scope.md).
- Verified 2026-07-04: 185 pages, 4.86M chars, all fetches 200.
