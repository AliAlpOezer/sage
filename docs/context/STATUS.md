# Status — sage

Last updated: 2026-07-28

## Current focus

W6 retrieval optimization (Day 37): baseline RAGAS scorecard is in — weakest metric is
`context_precision` (0.593) — and a reranking stage attacks it via the Cohere Rerank API
(see `docs/context/decisions.md`, "Reranker is Cohere Rerank API, not local BGE"). Full
plan and metric→technique mapping: `../../../ai-sprint-vault/Maps/W6 Optimization
Plan.md` (the vault this repo's exercises build against).

## In flight

- Reranking stage (Day 37): `Reranker` port + `none`/`bge`/`cohere` adapters +
  wide-retrieve plumbing in `service.answer()` are wired (see `decisions.md`). The
  `rerank-cohere` eval variant (`evals/harness.py`) is added but has not yet produced a
  scored comparison — see Blocked.

## Blocked

`rerank-bge` remains segfault-blocked (`qdrant_client`+torch in-process conflict —
`gotchas.md`).

## Next up

1. `rerank-cohere` generate phase failed 36/36 on two consecutive attempts (2026-07-28),
   both entirely `429 Too Many Requests` from OpenRouter on the generation model
   (`nvidia/nemotron-3-super-120b-a12b:free`) — not a Cohere or reranker issue; rerank runs
   before generation in the pipeline, so the failures are downstream of it. Fixed
   2026-07-28: `Settings.openrouter_api_key_2` (from `OPENROUTER_API_KEY_2`) is now read by
   both `OpenRouterGenerator` and `OpenRouterEmbedder` — on a 429 they move to the second
   key rather than retrying the same exhausted one. Rerun
   `uv run python -m sage.evals.harness run rerank-cohere` to get the scored comparison.
2. Once it scores: read `evals/runs/compare.md` for the `context_precision` delta vs the
   0.593 baseline (target: +0.05–0.10, recall flat). Keep/kill decision either way.
3. Hybrid search + RRF (Day 36) is next in the W6 plan's attack order — targets
   `context_recall` (0.679). **Correction (2026-07-28):** earlier notes claimed this was
   already half-built; verified false via `grep -r "bm25|rrf|hybrid|sparse" src` —
   zero hits. Unstarted, not partial.

## Recently landed

- Baseline RAGAS scorecard scored 36/36 triples (`evals/scorecard_baseline.md`, run
  2026-07-25): faithfulness 0.948, answer_relevancy 0.620, context_precision 0.593
  (weakest — most worst-cases are *correctly-refused* unanswerable questions scoring 0
  on relevancy, not a generation defect), context_recall 0.679.
- RAGAS eval harness + labeling tooling: judge/dataset/scorecard, label_helper +
  build_ragset, config-driven variant harness (top_k / assembly_order / chunker),
  evals/README (commit `ccc9100`, 2026-07-12).
- Earlier (per docs/context/sage.md, 2026-07-06): API+UI deploy verified end-to-end
  (FastAPI `/ask` behind the Atlas Next.js UI); generation model switched to a free
  OpenRouter model after the account went to negative balance.
