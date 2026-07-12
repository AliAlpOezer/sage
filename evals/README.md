# Sage evals

How Sage proves a change helped instead of vibing it. Everything here is measured
against the **naive RAG baseline** with a hand-labeled eval set and four RAGAS metrics.

## The pieces

| File | What it is |
|---|---|
| `candidates_v1.jsonl` | 90 AI-drafted candidate questions (empty `ground_truth`) — the raw material |
| `ragset_v1.worksheet.md` | Fillable worksheet: each candidate + real source excerpts + an `A[id]:` line |
| `ragset_v1.jsonl` | **The eval set** — hand-labeled triples (built from the worksheet). Not AI-generated. |
| `scorecard_baseline.md` | Day-31 baseline numbers (means + worst 5). The longitudinal record. |
| `runs/<name>/` | Per-variant run: `answers.jsonl` (cache), `scorecard.md`, `details.csv` |
| `runs/index.jsonl` | Append-only history — one row per scored run |
| `runs/compare.md` | Latest run of every variant, delta vs baseline |

## 1. Build the eval set (Day 30 — labeling is never delegated)

```bash
uv run python -m sage.evals.label_helper     # (re)build the worksheet w/ excerpts
# ... hand-write an answer on each A[id]: line you keep; leave blank to drop it ...
uv run python -m sage.evals.build_ragset      # worksheet -> ragset_v1.jsonl
```

Aim for 30–50 triples across `easy / hard / multi-hop / unanswerable`. For
`unanswerable` the correct ground truth is a refusal ("Not covered in the corpus.").

## 2. Baseline scorecard (Day 31)

```bash
uv run python -m sage.evals.scorecard                 # generate answers + score
uv run python -m sage.evals.scorecard --phase score   # re-score cached answers only
```

Then **hand-audit ~20% of the judge verdicts** against `scorecard_baseline_details.csv`
— the judge is a model too; without a human agreement check the scorecard drifts silently.

## 3. Change a knob → measure it (Day 32/33 harness)

```bash
uv run python -m sage.evals.harness list              # see the variants
uv run python -m sage.evals.harness run assembly-naive # generate + score a variant
uv run python -m sage.evals.harness ingest chunk-fixed # chunker variants re-index first
uv run python -m sage.evals.harness run chunk-fixed
uv run python -m sage.evals.harness compare           # -> runs/compare.md
```

Query-time knobs (`top_k`, `assembly_order`) reuse the baseline collection — cheap.
Chunker variants re-index into their own Qdrant collection (`ingest` first) — costs
embedding $.

## How to read a scorecard

Four metrics, all **higher-is-better (0–1)**. Which metric moves tells you *which
stage* to fix:

| metric | stage | a low score means |
|---|---|---|
| faithfulness | generation | answer isn't grounded in the retrieved context (hallucination) |
| answer_relevancy | generation | answer wanders off the question |
| context_precision | retrieval | retrieved junk alongside the good chunk |
| context_recall | retrieval | the needed chunk wasn't retrieved at all |

Rule of thumb: **retrieval metrics low + faithfulness OK** → the retriever is the
problem (chunking, top_k, reranking). **Generation metrics low + retrieval OK** →
prompt/model/assembly. Accept a knob only when its delta vs baseline is positive on
the metric you were targeting and not negative elsewhere.
