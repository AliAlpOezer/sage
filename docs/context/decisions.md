# Decisions — sage

One entry per settled decision, newest first — stops an agent from cheerfully
re-proposing something already rejected.

### OpenRouter keys rotate on 429 inside an httpx transport
Date: 2026-11-09 · Status: settled · revisit-if Alp stops wanting the free keys used
(credit was bought on key 2's account the same day; 402 now rotates too, so paid calls
find the funded key, and each `pool` - chat, embeddings - has its own key pointer)
Keys are numbered `OPENROUTER_API_KEY_1..N` in `.env` (the unnumbered
`OPENROUTER_API_KEY` is gone). One process-wide pointer marks the current key; a
key-level 429 moves it to the next number and the last wraps to `_1`, so later requests
start on the key that last worked. Lives in `src/sage/openrouter.py` as an httpx
transport, which is the one seam shared by the generator and embedder (plain httpx) and
the RAGAS judge (OpenAI SDK under langchain_openai, via injected `http_client`).
Rejected: a per-call key loop in each adapter (the old 2-key version; the judge never
rotated) and re-reading the env var name per request (same behaviour, more I/O).
A 429 whose body carries `error.metadata.provider_name` is the model's *provider*
throttling everyone ("rate-limited upstream"): it is returned without rotating, because
no key gets past it. Caveat accepted: OpenRouter's limits page says "Making additional
accounts or API keys will not affect your rate limits", so rotation may buy nothing.

### Reranker is Cohere Rerank API, not local BGE
Date: 2026-07-28 · Status: settled · revisit-if the bge/qdrant_client in-process crash
(see `gotchas.md`) gets fixed later
Originally chose local BGE (all-free, matches the Nemotron/OpenRouter-free pattern) but
it segfaults on this machine — `qdrant_client` and torch can't coexist in one process,
proven by bisection, not RAM. Switched to the `cohere` adapter (`adapters/rerank.py`,
Cohere Rerank v2, model `rerank-v3.5`): no local model, so it sidesteps the conflict
entirely. Cost accepted: needs a `COHERE_API_KEY` (trial keys support Rerank) and is a
paid external dependency, breaking the all-free stack for this one stage. The `bge`
adapter is left registered (unused, documented as blocked) for if the crash gets fixed.
Day-37 precision stage (baseline `context_precision`=0.593, weakest of the four RAGAS
metrics — see `evals/scorecard_baseline.md`). Chose local BGE cross-encoder over the
Cohere Rerank API to keep the stack all-free/no-API-key, matching the existing
Nemotron/OpenRouter-free pattern. Cost accepted: CPU inference is slow and the model is
a real download (~600MB); an API-based path (Cohere) would have been faster to stand up
but adds a paid external dependency. Implemented as a `Reranker` port (`ports.py`) with
`none` (passthrough, the baseline arm) and `bge` adapters (`adapters/rerank.py`),
selected via `SAGE_RERANKER` / `settings.reranker`, wide-retrieve via `retrieve_k=30`.
Date: 2026-07-06 · Status: settled · revisit-if OpenRouter balance goes positive again
Chose `nvidia/nemotron-3-super-120b-a12b:free` over paid `claude-sonnet-4-6` because the
OpenRouter account went to -$0.14 balance. `openai/gpt-oss-120b:free` was tried first but
its free upstream provider was heavily throttled (1/4 requests returned 200); nemotron
was reliable (3/3) with good grounded, cited answers. Cost accepted: `:free` models are
best-effort upstream — reliability varies day to day. Question embedding is still the
one remaining paid call (~$2e-7/query, cheap enough under the negative balance).

### Qdrant client is memoized as a process-long singleton, not built per request
Date: 2026-07-06 · Status: settled
`factory.make_vector_store` caches one client per (vector_store, qdrant_path,
collection), because embedded Qdrant is single-process/file-locked and a per-request
client left the lock held by a dead traceback whenever a request raised, wedging later
requests. Cost accepted: the API now holds the lock for its entire lifetime — it must be
stopped before (re)ingesting. `factory.reset_vector_store_cache()` exists for tests.

### Ingestion is idempotent per-chunk but never prunes
Date: 2026-07-04 (documented 2026-07-06) · Status: settled
Chunk id = `sha256(source_url + text)` formatted as a UUID (Qdrant requires UUID/int
ids), so re-running ingest upserts each chunk in place rather than duplicating it. Cost
accepted: it only upserts/overwrites, never deletes — when a page's text changes, its
old chunks keep their old ids and linger as orphans, so stored vector count can exceed
the chunk count just embedded. A clean rebuild requires deleting `data/qdrant/` first.

### Corpus source is sitemap.xml, not llms.txt
Date: 2026-07-04 · Status: settled
Chose the sitemap (1418 URLs, append `.md` for markdown) over `llms.txt` because
`llms.txt` hard-truncates at 100K chars and omits the entire `/oss/` section entirely.

### Corpus scope is `/oss/python/` only
Date: 2026-07-04 · Status: settled · revisit-if the JS docs become in-scope
185 of 1418 sitemap pages (~1.2M tokens, ~$0.025 to embed) — the LangChain 1.0 Python
docs the sprint targets. Excludes the JS mirror. Configurable via `SAGE_DOCS_URL_PREFIX`.

### Built from scratch, no RAG framework
Date: 2026-07-04 · Status: settled
The point of the project is learning the RAG abstractions by hand, so no
LangChain-the-framework is used for the pipeline itself — only `httpx` directly against
OpenRouter's OpenAI-compatible API, so raw request/response shapes stay visible.
(`langchain-*` packages appear only as a dev `eval` dependency, for RAGAS.)

### Vector store: Qdrant embedded local mode first, pgvector planned second
Date: 2026-07-04 · Status: settled · revisit-if pgvector adapter gets built (unbuilt as
of 2026-07-21)
Chosen because it needs no Docker daemon (Docker is installed but usually stopped on
this machine). Cost accepted: single-process file lock and no HNSW tuning — exact search
only, fine at this corpus size.

### Labeling the eval set is never delegated to AI
Date: 2026-07-12 · Status: settled
`evals/candidates_v1.jsonl` (90 questions) is AI-drafted, but turning it into
`ragset_v1.jsonl` requires a human to hand-write each `A[id]:` line on the worksheet;
blank lines are dropped. Rationale (commit message): the eval set is the ground truth
the judge is checked against — if AI writes both, agreement is meaningless.
