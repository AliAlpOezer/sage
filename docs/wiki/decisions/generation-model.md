---
type: decision
title: Generation — claude-sonnet-4-6 via OpenRouter, top_k=5
description: Answer-generation model and context size for the query loop; exercised end-to-end 2026-07-04.
resource: src/sage/config.py
tags: [generation, query, cost]
timestamp: 2026-07-04T00:00:00Z
---

## Context
The last pipeline stage: given the question and the top-k retrieved chunks,
generate a grounded answer with citations. Implemented in Bucket 3
([component](../components/generator.md)); context is arranged edges-first
(strongest chunk opens the prompt, second-strongest closes it — the
lost-in-the-middle mitigation, `src/sage/assembly.py`).

## What we chose
`SAGE_GENERATION_MODEL=anthropic/claude-sonnet-4-6` via OpenRouter (same key
as embeddings), `SAGE_TOP_K=5` chunks as context.

## Alternatives & trade-offs
- **Cheaper/faster (Haiku-class)** — often plenty for *grounded* QA: the
  answer is in the provided context, not the model's head, so raw model
  knowledge matters less than instruction-following. Worth measuring in the
  10-question eval; the swap is one env line.
- **Bigger models** — better synthesis on multi-chunk answers at higher cost
  and latency; unlikely to be the bottleneck while retrieval is naive.
- **top_k trade-off** — too low misses the evidence; too high buries it: the
  "lost in the middle" effect (models attend most to the start and end of the
  context). Day 26 topic — context assembly should place the strongest chunks
  at the edges, not buried mid-context.

## Why this serves the goal
A strong default that keeps the eval focused on retrieval failures (the
learning target), not generation failures.

## Revisit when
Bucket 4's failure log separates retrieval misses from generation misses —
then compare models/k on the same questions.
