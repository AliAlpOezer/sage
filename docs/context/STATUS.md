# Status - sage

Last updated: 2026-11-09

## Current focus

Turning sage into a showcase (decided 2026-11-09): hybrid retrieval (BM25 sparse + HNSW
dense in Qdrant) plus GraphRAG on Neo4j, fused with the hand-written RRF. **Cloudflare
hosting is deferred**: develop locally, free services only. First unblock evals, since
every retrieval change has to be scored to count.

## State (verified 2026-11-09)

- Golden set `evals/ragset_v1.jsonl` is done: 36 hand-labeled triples (17 easy,
  14 unanswerable, 4 multi-hop, 1 hard). Empty `source_urls` on u001-u014 is correct.
- The July-August W6 work (reranker port, BM25 + RRF hybrid, contextual retrieval,
  OmniRoute generator) and the 2026-11-09 OpenRouter key rotation are committed on
  branch `w6-hybrid-rerank-contextual` (2026-11-09; not pushed, not merged; it also
  carries the 4 unmerged commits of `add-context-pack`). 34 tests pass, ruff clean.
  Still to do: a separate repo-wide `ruff format` commit (23 of 36 files do not match
  the global ruff config; the repo has no `[tool.ruff]`).
- OpenRouter is the working route (2026-11-09): `$10` credit bought on the account of
  `OPENROUTER_API_KEY_2` (total_credits 10, so 1,000 free-model requests/day). `.env` has
  `SAGE_GENERATOR=openrouter` and `SAGE_JUDGE_PROVIDER=openrouter`. Paid query embeddings
  402 on the other keys and rotate to key 2 (own `embeddings` key pointer); chat calls use
  `:free` models and walk keys 1..8, so credit is only spent on embeddings (cents).
  Verified with a real `sage.ask` question end to end.
- Hybrid vs baseline is **unresolved**: hybrid (2026-08-04) scored faithfulness 0.880,
  answer_relevancy 0.650, context_precision 0.564, context_recall 0.629 vs baseline
  0.948 / 0.620 / 0.593 / 0.679, but generator and judge both changed between the runs.
  Re-score both under one judge before any keep/kill call.

## Blocked

- `rerank-bge` stays segfault-blocked (`gotchas.md`).

## Next up

1. Finish the same-judge re-score (judge `nvidia/nemotron-3.5-super-vl:free`). Scoring is
   resumable since 2026-11-09 (`evals/runs/<variant>/scores.jsonl`, per-sample, per-judge).
   State when the run was killed for low RAM: baseline 36/36 scored once, 23 complete
   (13 have a NaN metric and get retried); hybrid just started. Resume with
   `uv run python -m sage.evals.harness run baseline --phase score`, then the same for
   `hybrid`. Run it in a plain terminal: Claude Code reaps background jobs when this
   3.6 GB machine runs out of memory.
2. Then score `rerank-cohere` and the contextual arms against that same judge.
3. Alp labels ~20 more multi-hop questions: with 4 of 36, a GraphRAG win cannot show up
   in the scorecard. (Labeling is never delegated, see `decisions.md`.)
4. Native hybrid in Qdrant (sparse vectors with IDF + dense HNSW in one collection);
   the in-memory `rank_bm25` index rebuilds per process.
5. Neo4j graph from doc structure first (page links, heading tree, class mentions,
   zero LLM cost), LLM entity extraction as the paid comparison arm; a GraphRetriever
   port feeding RRF as a third list. Run a `system-design` pass first.
6. Machine limit: 3.6 GB RAM, Docker not running. Local Neo4j + Qdrant server will not
   fit; the free managed tiers (AuraDB Free, Qdrant Cloud free) are the realistic
   "free" option, and both pause when idle.
