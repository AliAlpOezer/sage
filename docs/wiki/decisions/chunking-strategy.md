---
type: decision
title: Chunking — recursive, structure-aware, hand-written
description: Split at markdown headings, greedily pack paragraphs to 1800 chars, hard-split oversized blocks with 200-char overlap.
resource: src/sage/adapters/chunkers.py
tags: [ingestion, retrieval-quality, hand-written]
timestamp: 2026-07-04T00:00:00Z
---

## Context
Pages must be split before embedding. Two hard constraints force this: the
LLM's context window can't hold 185 pages, and — less obvious — **an embedding
vector is a summary of everything in the text**. Embed a 10,000-word page and
the vector is a muddy average of twenty topics; embed one focused paragraph and
the vector is sharp. See [what is an embedding](../concepts/embeddings.md).

## What we chose
A recursive, structure-aware chunker, **written by hand** (sprint protocol —
own every retrieval decision): split at markdown headings (keeping each heading
with its section) → sections over `SAGE_CHUNK_MAX_CHARS=1800` are split on
paragraph boundaries and greedily re-packed → single blocks still over the
limit are hard-split with a sliding window, `SAGE_CHUNK_OVERLAP_CHARS=200`
overlap. Measured result: 185 pages → **4836 chunks**.

## How it works
"Recursive" = descend from coarse structure to fine: headings first (a heading
names its section — separating them orphans the text), then paragraphs, then
raw character windows only as a last resort. The overlap exists so a sentence
cut at a hard boundary still appears intact in the neighboring chunk —
insurance against losing the exact sentence that answers a question.

## Alternatives & trade-offs
- **Fixed-size sliding window** — simplest, uniform sizes; ignores structure,
  slices mid-sentence, welds unrelated sections together. The baseline this
  chunker gets measured against in W5.
- **Semantic chunking** — embed every sentence, split where consecutive
  similarity drops (a topic-shift detector). Can win on unstructured prose;
  costs an extra embedding pass and is harder to reason about. On markdown docs
  it is mostly redundant: **the headings already are the semantic boundaries,
  written by a human.**
- **Whole-page chunks** — maximal context per hit, but retrieval degrades to
  "which page" and the muddy-vector problem returns.

**Size trade-off** (1800 chars ≈ 450 tokens): smaller → sharper vectors, more
precise hits, fragmented context; bigger → richer context, blurrier vectors.
300–500 tokens is the conventional starting zone — W5 measures instead of
trusting convention. Chars (not tokens) as the unit: simpler, no tokenizer
dependency; fine at these sizes.

## Why this serves the goal
Hand-writing the chunker was the sprint's explicit learning exercise; its
executable spec lives at `tests/test_chunker.py` (8 tests).

## Revisit when
W5 chunking comparison — register alternatives as new adapters
(`@register_chunker("fixed")`, `"semantic"`) and measure head-to-head.
