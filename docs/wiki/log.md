# Documentation log (append-only)

## 2026-07-04 — Bucket 3: query loop live
- Updated components/generator.md (planned → implemented: OpenRouterGenerator,
  grounded-only system prompt, citation contract), decisions/generation-model.md
  (exercised; edges-first assembly note), state/current-state.md (loop verified,
  14 tests), index one-liners.
- Evidence: pytest (14 passed), live query "How do I create an agent with
  create_agent..." → cited answer; source order confirmed edges-first
  arrangement (top score first, second-best last).

## 2026-07-04 — Initial bundle: Day 25 ingestion milestone
- Created the bundle: index, this log, 1 state page, 9 decision pages,
  5 component pages, 2 concept pages (17 files).
- Captured the decision-by-decision explainer from the Day 25 session:
  corpus source/scope, chunking, embedding strategy, similarity metric,
  vector store, chunk identity, generation defaults, ports/factory
  architecture.
- Evidence used: git log (d95b070, 5190da1, e889968), docs/context/sage.md,
  live ingest output (185 pages / 4836 chunks / 4820 vectors / dim 1536,
  two runs identical), pytest output (11 passed), corpus measurement
  (4.86M chars ≈ 1.2M tokens ≈ $0.025 per ingest).
- Known-stale risk: generator pages describe planned Bucket 3 defaults;
  update decisions/generation-model.md and components/generator.md when the
  adapter lands.
