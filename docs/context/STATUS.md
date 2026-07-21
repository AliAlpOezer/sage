# Status — sage

Last updated: 2026-07-21

## Current focus

Sprint-2 measurement week: RAGAS eval harness is built; producing the hand-labeled
eval set (`ragset_v1.jsonl`) so runs can actually be scored.

## In flight

<!-- No open PRs tracked in this repo; single-branch history so far. -->

## Blocked

Eval runs (`sage.evals.scorecard`, `sage.evals.harness run …`) are blocked on
`evals/ragset_v1.jsonl` not existing yet — only `ragset_v1.worksheet.md` (fillable) and
`candidates_v1.jsonl` (90 AI-drafted candidates, ungraded) are present. Labeling is
explicitly not delegated to AI (per the eval harness commit message); a human must fill
in the `A[id]:` lines on the worksheet, then run `sage.evals.build_ragset`.

## Next up

1. Hand-label the worksheet into `evals/ragset_v1.jsonl` (30-50 triples, easy/hard/
   multi-hop/unanswerable).
2. Run `sage.evals.scorecard` for the baseline scorecard, then hand-audit ~20% of judge
   verdicts against the details CSV.
3. Use `sage.evals.harness run <variant>` to compare knobs (top_k, assembly order,
   chunker) against the baseline.

## Recently landed

- RAGAS eval harness + labeling tooling: judge/dataset/scorecard, label_helper +
  build_ragset, config-driven variant harness (top_k / assembly_order / chunker),
  evals/README (commit `ccc9100`, 2026-07-12).
- Earlier (per docs/context/sage.md, 2026-07-06): API+UI deploy verified end-to-end
  (FastAPI `/ask` behind the Atlas Next.js UI); generation model switched to a free
  OpenRouter model after the account went to negative balance.
