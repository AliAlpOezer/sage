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

### Loading a local BGE/torch reranker crashes the process (segfault, no traceback)
Cause: `qdrant_client` (Rust extension) and `sentence-transformers`/torch cannot coexist
in the same process on this machine. Confirmed by bisection (2026-07-28): a plain
`CrossEncoder` load succeeds in complete isolation, but crashes (exit 139, no Python
traceback — a hard native crash, not `MemoryError`) the moment `sage.adapters` has been
imported (which imports `qdrant_store` → `qdrant_client`) in the same process — even
before any Qdrant client is constructed, and regardless of which loads first. Not RAM
(reproduces on a single query, not just after many); not an OpenMP duplicate-runtime
conflict (`KMP_DUPLICATE_LIB_OK=TRUE` doesn't help).
Fix: none found yet. Local `bge` reranker is unusable as long as `qdrant_client` is
imported in-process. Options not yet tried: run the reranker in a separate subprocess;
switch the vector store to Qdrant's pure-REST client mode (if that avoids importing the
native extension); or use the `cohere` reranker adapter instead (API, no local import).
Until one of these is verified, treat `SAGE_RERANKER=bge` as broken on this machine.

### Every free LLM route is now exhausted or dead — an eval run cannot complete (2026-08-12)
Symptom: `harness run <variant> --phase score` starts, scores 20-40 of 144 jobs, then fills
with exceptions and never writes a scorecard.
Cause: all three routes failed on the same day, for three unrelated reasons.
- **OmniRoute** (`SAGE_JUDGE_PROVIDER=omniroute`, the documented default) starts fine and
  listens on `:20128`, but has **zero connected credentials** — the log says
  `[AutoRefreshDaemon] Started — checking 0 credentials`, and every alias resolves to
  `matched no connected models; returning an empty pool`. Requests then **hang until timeout
  rather than erroring**, so it looks like a slow run, not a broken one. Diagnose with
  `tail ~/.omniroute/logs/application/app.log`, not by curling `/v1/models` (that endpoint
  hangs too).
- **OpenRouter** returns `402 Insufficient credits — this account never purchased credits`.
  This kills `answer_relevancy` outright, because question embedding is hardwired to
  OpenRouter regardless of judge provider. It also blocks any *generate* phase, since query
  embedding uses the same route.
- **Groq** free tier is **100,000 tokens per day**, org-wide. One RAGAS pass over 36 triples
  is 144 judge jobs and consumes essentially the whole daily budget — the 2026-08-12 run hit
  `TPD Limit 100000, Used 99058` at roughly job 30 of 144. Groq cannot finish a single full
  eval run on the free tier. `GROQ_API_KEYS` (multi-key) splits rpm, not TPD, so extra keys
  in the same org do not help.
- **Gemini** was tried next and **also failed** — do not repeat this. `gemini-2.5-flash` on the
  free tier reached **139 of 144 jobs in 27 minutes**, then hit
  `RESOURCE_EXHAUSTED / GenerateRequestsPerDayPerProjectPerModel-FreeTier, quotaValue: 20` and
  never wrote a scorecard. Failing at 97% is the worst case: it burns the full daily quota *and*
  produces nothing, because the scorecard is only written after all jobs succeed.
Fix: **none of the four free routes can complete one RAGAS pass as of 2026-08-12.** Sizing
constant for planning: one pass over the 36-triple `ragset_v1` is **144 judge jobs** (36 × 4
metrics) and takes ~27 min wall-clock at free-tier rates. Budget against that number before
picking a provider.
Options, in order of how much they actually buy:
1. Put a small amount of credit on OpenRouter. It fixes the judge *and* `answer_relevancy` *and*
   unblocks the generate phase, all at once. Everything else is a workaround.
2. Score fewer triples per pass, or fewer metrics, so a pass fits in a free daily quota.
3. Make the harness checkpoint partial scores so a quota kill at 97% is resumable rather than
   total loss. The generate phase already caches per-answer and resumes; the score phase does
   not, and that asymmetry is what made today a write-off.
Whichever route: `answer_relevancy` stays NaN until OpenRouter has credit, because question
embedding is hardwired there regardless of judge. The other three metrics are judge-LLM only,
and `context_precision` — the W6 target — is one of them, so retrieval work is not blocked by
the embedding gap alone.

Update 2026-11-09 (measured live): 8 OpenRouter keys now rotate on 429
(`OPENROUTER_API_KEY_1..8`, `src/sage/openrouter.py`), all free tier.
- Free model ids rot. The old default `nvidia/nemotron-3-super-120b-a12b:free` returns 404;
  `nemotron-3-ultra-550b-a55b:free` timed out (504 / read timeout);
  `google/gemma-4-31b-it:free` was "rate-limited upstream". Working for generation and as
  RAGAS judge: `nvidia/nemotron-3.5-super-vl:free` (now the openrouter default). List the
  current ones with `GET https://openrouter.ai/api/v1/models`, keep ids ending `:free`.
- A 429 body with `error.metadata.provider_name` is the provider throttling everyone;
  rotating keys does not help, so the transport returns it at once.
- OpenRouter can answer HTTP 200 with an `error` body and no `choices` (upstream 504);
  the generator now raises a clear error instead of `KeyError: 'choices'`.
- Embeddings: free embedding models exist now; `nvidia/nemotron-3.5-embed-1b:free`
  works (2048 dims). The paid `text-embedding-3-small` still 402s on every key.
- OmniRoute was not running on 2026-11-09 (`:20128` refused).

### Re-scoring cached answers without regenerating them
`harness run <variant> --phase score` scores whatever is already in
`evals/runs/<variant>/answers.jsonl`, so a judge can be swapped and re-run without paying for
generation again. This also allows scoring an *older* answer set: the original 2026-07-25
baseline answers are preserved at `evals/baseline_answers_v1.jsonl`, so
`cp evals/baseline_answers_v1.jsonl evals/runs/baseline/answers.jsonl` then `--phase score`
re-scores the exact answers behind the published baseline scorecard. That isolates a judge
change from a generation change — the right move when the question is "was the old number an
artifact of the judge?" rather than "is the new pipeline better?".

### Chunker variant in the eval harness needs a re-index before scoring
Cause: a chunker variant produces different chunks/ids than the baseline collection —
scoring without re-indexing scores against the wrong collection.
Fix: run `sage.evals.harness ingest <variant>` first (costs embedding $), then `run
<variant>`. Query-only knobs (`top_k`, `assembly_order`) reuse baseline, no re-index.
