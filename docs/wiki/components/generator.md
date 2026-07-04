---
type: component
title: Generator (port) — not yet implemented
description: Bucket 3 work; answers a question grounded only in the retrieved chunks, with citations.
resource: src/sage/ports.py
tags: [generation, port, planned]
timestamp: 2026-07-04T00:00:00Z
---

Port: `Generator.generate(question, context: list[ScoredChunk]) -> str` —
answer grounded ONLY in the provided chunks, citing source URLs.

**Status: port defined, no adapter yet** — Bucket 3 builds
`OpenRouterGenerator` plus `ask.py` (query embedding → top-k → context
assembly → answer). Defaults already configured: `SAGE_GENERATOR=openrouter`,
`SAGE_GENERATION_MODEL=anthropic/claude-sonnet-4-6`, `SAGE_TOP_K=5`.

Context-assembly note for the implementation: order the strongest chunks at
the edges of the prompt (lost-in-the-middle), and instruct the model to answer
"I don't find this in the docs" rather than free-styling when context is
insufficient. Decision & alternatives: [generation-model](../decisions/generation-model.md).
