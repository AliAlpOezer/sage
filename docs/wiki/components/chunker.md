---
type: component
title: Chunker (port) — RecursiveChunker
description: Hand-written structure-aware splitter; the port W5 chunking comparisons plug into.
resource: src/sage/adapters/chunkers.py
tags: [ingestion, port, hand-written]
timestamp: 2026-07-04T00:00:00Z
---

Port: `Chunker.chunk(page: Page) -> list[Chunk]` — document order, positions
sequential. Selected by `SAGE_CHUNKER` (default `recursive`).

Current adapter: **RecursiveChunker, hand-written by the user** (sprint
protocol). Headings → paragraph packing → hard split with overlap; tuned by
`SAGE_CHUNK_MAX_CHARS=1800`, `SAGE_CHUNK_OVERLAP_CHARS=200`.

- Executable spec: `tests/test_chunker.py` (8 tests — empty/short pages,
  heading splits, max-size, sequential positions, exact overlap on hard
  splits, no blank chunks, unicode).
- Measured 2026-07-04: 185 pages → 4836 chunks.
- Design rationale and alternatives: [chunking-strategy](../decisions/chunking-strategy.md).
- Implementation notes from review: chunks are frozen dataclasses — positions
  are assigned at construction (`position=len(chunks)`), never mutated after.
