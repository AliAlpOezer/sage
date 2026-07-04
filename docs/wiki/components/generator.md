---
type: component
title: Generator (port) — OpenRouterGenerator
description: Grounded answering over numbered excerpts via OpenRouter chat completions, with inline citations.
resource: src/sage/adapters/openrouter_generator.py
tags: [generation, port]
timestamp: 2026-07-04T00:00:00Z
---

Port: `Generator.generate(question, context: Sequence[ScoredChunk]) -> str`.
Selected by `SAGE_GENERATOR` (default `openrouter`); model by
`SAGE_GENERATION_MODEL` (default `anthropic/claude-sonnet-4-6`).

Current adapter: **OpenRouterGenerator** — renders the context as numbered
excerpts (`[1] Title (url) + text`), sends a system prompt enforcing
grounded-only answering ("answer ONLY from the excerpts; cite [n] inline; if
the excerpts don't contain the answer, say exactly that"), retries on
429/5xx. `max_tokens=1024`.

Citation contract: excerpts are numbered in the order *received*; the caller
([ask.py](../../..//src/sage/ask.py)) prints its source list from the same
order, so `[n]` in the answer always matches the printed source `[n]`.

Context ordering happens BEFORE the generator, in `src/sage/assembly.py`
(edges-first — see [generation-model](../decisions/generation-model.md) on
lost-in-the-middle).

Verified 2026-07-04: end-to-end query about `create_agent`/LangGraph runtime
returned a grounded, correctly-cited answer from 5 retrieved chunks.
