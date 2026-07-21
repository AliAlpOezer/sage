# Gotchas — sage

Traps that cost someone real time. Routed to first on any "it's broken / slow / weird"
task — lead with the **symptom**.

### API request fails with "already accessed by another instance" (Qdrant)
Cause: embedded Qdrant allows only one process at a time and file-locks `data/qdrant/`.
Ingestion and the API both open that store, and the API holds the lock (a memoized
singleton client) for its whole process lifetime. Also: on Windows the venv `python.exe`
is a launcher stub, so one `uvicorn` process shows as **two** OS processes — killing
only one leaves an orphan holding the lock.
Fix: stop the API server (kill both processes) before running ingest, or vice versa.

### `uv run uvicorn ...` fails with `os error 5` on Windows
Cause: the bare-console-script form of uvicorn is broken on this box.
Fix: run `uv run python -m uvicorn sage.api:app --port 8000` instead — `python -m`
works, the console-script entry point does not.

### Re-ingesting an unchanged corpus doesn't reproduce the exact same vector count
Cause: ingestion is idempotent per-chunk (same content → same id → overwrite) but never
prunes. If a page's text changed between runs, its old chunks linger as orphans, so
stored count can exceed the chunk count just embedded (observed 4893 stored > 4842
chunked on one re-ingest).
Fix: for a clean rebuild, delete `data/qdrant/` then re-run `python -m sage.ingest`.
Counts also drift release to release since the live docs change — don't assume a
mismatch is a bug before checking that.

### RAGAS eval runs are slow, and a free judge model can return NaN metrics
Cause: OpenRouter's free tier caps at 8 req/min, so judge calls run serially — slow is
the rate limit, not a hang. A free judge can also be flaky on RAGAS's structured output,
producing NaN scores.
Fix: set `SAGE_JUDGE_PROVIDER` to `groq` or `gemini` (with the matching API key) for a
real free tier. Question embedding still goes through OpenRouter regardless (tiny paid
call, not the bottleneck).
<!-- TODO(alp): no eval run has completed yet — confirm actual runtime/NaN rate once one runs. -->

### `sage.evals.scorecard` / `sage.evals.harness run` has nothing to score
Cause: those need `evals/ragset_v1.jsonl`, which doesn't exist until someone hand-labels
`evals/ragset_v1.worksheet.md` and runs `sage.evals.build_ragset`. Only the AI-drafted
`candidates_v1.jsonl` and the blank worksheet are checked in.
Fix: not a bug, current project state. Never auto-generate the labels; labeling is
explicitly not delegated to AI.

### Chunker variant in the eval harness needs a re-index before scoring
Cause: a chunker variant produces different chunks/ids than the baseline collection —
scoring without re-indexing scores against the wrong collection.
Fix: run `sage.evals.harness ingest <variant>` first (costs embedding $), then `run
<variant>`. Query-only knobs (`top_k`, `assembly_order`) reuse baseline, no re-index.
