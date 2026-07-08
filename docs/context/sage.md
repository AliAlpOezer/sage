# Sage (RAG over LangChain docs) — Context Pack
Updated: 2026-07-06

## Goal & Core Decision
Learning-first RAG over docs.langchain.com, built from scratch in Python behind
swappable ports (Embedder, VectorStore, Generator) so approaches can be compared
head-to-head. Done-when (Day 25): 10 real questions answered end-to-end, failures logged.

## Requirements
- [must] Ports + config-keyed factory; swap backends via .env only
- [must] Idempotent ingestion (chunk id = content hash → re-run gives same vector count)
- [must] Query loop: embed → top-k → context assembly → answer with source URLs
- [must] Adapter set #1: OpenRouter embeddings + Qdrant local mode + OpenRouter generation
- [should] Async embedding with bounded concurrency (semaphore)
- [should] pgvector as adapter #2 proving the abstraction
- [could] Local sentence-transformers embedder as adapter #3
## Non-goals
- Reranking, query transforms, measured evals (W5–6), UI (Day 26+), LangChain-the-framework

## Decisions (with rationale)
- From scratch, no RAG framework — user is building the abstractions to learn them. (2026-07-04)
- httpx over OpenAI SDK for OpenRouter — see raw request/response shapes. (2026-07-04)
- OpenRouter one key for embeddings AND generation — OpenRouter now has an
  OpenAI-compatible /api/v1/embeddings endpoint. (2026-07-04)
- Qdrant first via qdrant-client local mode (no Docker needed), pgvector second.
  Docker installed (29.6.1) but daemon usually stopped. (2026-07-04)
- Corpus index: sitemap.xml, NOT /llms.txt — llms.txt hard-truncates at 100K chars
  and omits the entire /oss/ section. Sitemap has 1418 URLs; append .md for markdown. (2026-07-04)
- Scope: /oss/python/ (185 pages, ~1.2M tokens ≈ $0.025 to embed) — the LangChain 1.0
  Python docs the sprint targets; excludes the JS mirror. Configurable. (2026-07-04)
- Chunker is a fourth port with its own registry — W5 measures chunking strategies
  head-to-head, same swap mechanism as the other backends. (2026-07-04)
- Embedder port has no dimension property — ingest derives dims from len(vectors[0]);
  no per-model dimension table to maintain. (2026-07-04)
- Chunk ids: sha256(source_url + text) formatted as UUID — Qdrant only accepts
  UUID/int point ids; deterministic id gives idempotent upserts. (2026-07-04)
- Embedding model: openai/text-embedding-3-small (1536 dims, cosine). Generation:
  anthropic/claude-sonnet-4-6. Both are .env values. (2026-07-04)
- Ingest is idempotent per-chunk but NON-PRUNING: it upserts/overwrites, never
  deletes. On corpus drift, changed pages leave orphan vectors (count grew
  4820→4893 on 2026-07-06 re-ingest, 4842 chunks). Clean rebuild = delete
  data/qdrant/ then re-run. README documents this. (2026-07-06)
- Qdrant local mode is single-process (file lock on data/qdrant). Run only ONE
  writer/server at a time. Windows venv python.exe is a LAUNCHER STUB that spawns
  the base interpreter, so one uvicorn shows as TWO processes (stub + child) —
  kill both when stopping or an orphan keeps the lock and later starts 500 with
  "already accessed by another instance". (2026-07-06)
- FIX (2026-07-06): make_vector_store now memoizes one store per (vector_store,
  qdrant_path, collection) in factory._VECTOR_STORE_CACHE — a process-long-lived
  singleton, the right model for embedded qdrant. Previously it built a client
  per request and leaned on GC to free the lock; a request that raised (e.g. the
  402) kept the client alive via the traceback and wedged all later requests with
  the lock error. Now failures surface the real upstream error, no wedge.
  factory.reset_vector_store_cache() drops it (tests / clean rebuild). Consequence:
  the API holds the lock for its lifetime → stop it before (re)ingesting. 14 tests pass.
- Generation model switched claude-sonnet-4-6 → nvidia/nemotron-3-super-120b-a12b:free
  (user: no paid models). User suggested openai/gpt-oss-120b:free but its free upstream
  provider (OpenInference) is heavily throttled (1/4 requests return 200); nemotron
  was reliable (3/3) and gives good grounded cited answers. Set via
  SAGE_GENERATION_MODEL in .env; config.py default unchanged. :free models are
  best-effort/rate-limited upstream — reliability varies by day. (2026-07-06)

## Current State
- Done: Buckets 1–3. Full RAG loop verified live 2026-07-04:
  ingest (185 pages → 4836 chunks → 4820 vectors, idempotent, ~$0.025) and
  ask.py (embed → top-k → edges-first assembly → cited answer). 14 tests pass.
  Chunker was hand-written by the user (sprint protocol).
- Done (Day 26, 2026-07-05): HTTP layer for the Atlas UI. Query loop extracted
  from ask.py into `service.answer()` (returns Answer{answer, sources[Source]}
  where Source = n/title/url/score/text). `api.py` = FastAPI POST /ask + /health.
  ask.py now a thin CLI over service. Deps +fastapi +uvicorn. CLI + 14 tests
  still pass; /ask verified live end-to-end from the Next.js proxy.
  Run: `uv run python -m uvicorn sage.api:app --port 8000`
  (NOTE: `uv run uvicorn ...` fails with os error 5 on this box — use `python -m`.)
- Deep documentation: docs/wiki/ (OKF-style bundle, maintained via the
  /document skill at dev/.claude/skills/document/).
- Done (Day 27, 2026-07-06): DEPLOY. Both services brought up live — Sage API
  :8000 + Atlas UI :3000 — and E2E cited answers verified through the UI proxy
  (browser → /api/ask → Sage) with 3 real questions. README rewritten for
  reproducibility: added "Build the index" (accurate idempotency + orphan note),
  "Serve the API + UI", the `python -m uvicorn` Windows gotcha (NOT `uv run
  uvicorn` → os error 5); fixed stale cmd in atlas/.env.local. Idempotent
  re-ingest ran clean (exit 0). Tests 14/14.
- BALANCE (2026-07-06): OpenRouter at −$0.14 (0 credits). Generation switched to a
  FREE model (decision below) → /ask works again, verified live with a cited answer.
  Question-embedding still uses PAID openai/text-embedding-3-small but is cheap
  enough (~$2e-7/query) to slip under the negative balance for now — it is the ONE
  remaining paid call. Fully-free = local sbert embedder (adapter #3, unbuilt) +
  full re-ingest (new dims → new/wiped collection).
- Next (decide): drop the last paid call — local sbert embedder (adapter #3) +
  re-ingest — OR accept the ~$2e-7/query embedding cost. Then pgvector adapter
  (needs Docker daemon); ask 10 real questions + log failures (day25-failure-log.md).

## Open Questions
- Exact /oss/ page count and token volume (measure during Bucket 2).
- pgvector schema (Bucket 5): single table, vector column dims fixed per embedder.

## Key Files / Interfaces
- `src/sage/ports.py` — Chunker (chunk(Page) -> list[Chunk]), Embedder (async embed),
  VectorStore (ensure_collection/upsert/search/count), Generator (generate)
- `src/sage/loader.py` — sitemap parse + concurrent page fetch -> list[Page]
- `src/sage/ingest.py` — load → chunk → embed → upsert (run: python -m sage.ingest)
- `src/sage/assembly.py` — arrange(ranked) edges-first (lost-in-the-middle)
- `src/sage/service.py` — answer(question, k) -> Answer{answer, sources}; shared
  by CLI + API. Raises EmptyIndex when the store is empty.
- `src/sage/api.py` — FastAPI app: POST /ask {question,k?} -> {answer, sources},
  GET /health. CORS allow_origins=["*"] (dev only — pin before non-local use).
- `src/sage/ask.py` — CLI over service.answer (run: python -m sage.ask "q" [-k N])
- `src/sage/factory.py` — register_* decorators + make_* builders keyed by Settings
- `src/sage/config.py` — frozen Settings dataclass, Settings.from_env()
- `src/sage/models.py` — Chunk (with make_id), ScoredChunk
- `src/sage/adapters/` — one module per backend, self-registering
