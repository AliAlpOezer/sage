# Architecture — sage

Budget: 900 tokens. This file answers "where does X live" and "how does X flow" without
the agent having to read the tree. Self-contained — never defer to another context file.

## Shape

Sage is a from-scratch RAG (retrieval-augmented generation) system over the LangChain
docs, built as a learning project. Two pipelines: **ingestion** (load pages from
docs.langchain.com's sitemap → chunk → embed → upsert into a vector store) and **query**
(embed the question → top-k vector search → assemble context → generate a cited
answer). Every stage — chunker, embedder, vector store, generator — is a `Protocol`
("port") in `src/sage/ports.py`; concrete adapters live in `src/sage/adapters/` and
self-register with a factory (`src/sage/factory.py`) keyed by names read from `.env`
(via `src/sage/config.py`'s `Settings.from_env()`). Swapping a backend means writing one
adapter and registering it — nothing else changes. The query loop is shared by a CLI
(`sage.ask`) and a FastAPI HTTP layer (`sage.api`) consumed by a separate Next.js UI
(`../atlas`, sibling repo, out of scope here) via `POST /ask`.

## Map

| Path | Holds |
|---|---|
| `src/sage/ports.py` | The four Protocols: `Chunker`, `Embedder`, `VectorStore`, `Generator`. |
| `src/sage/adapters/` | One module per backend, self-registering with the factory (OpenRouter embedder/generator, Qdrant store, chunkers). |
| `src/sage/factory.py` | `register_*` decorators + `make_*` builders keyed by `Settings`; also caches the Qdrant client as a process-long singleton per (store, path, collection). |
| `src/sage/config.py` | Frozen `Settings` dataclass, `Settings.from_env()` — all `.env` / `SAGE_*` knobs. |
| `src/sage/loader.py` | Sitemap parse + concurrent markdown-page fetch → `Page` objects. |
| `src/sage/ingest.py` | Ingestion pipeline entry point: `python -m sage.ingest`. |
| `src/sage/assembly.py` | Arranges ranked chunks into context ("edges-first" ordering, addressing lost-in-the-middle). |
| `src/sage/service.py` | `answer(question, k) -> Answer{answer, sources}` — the shared query loop used by both CLI and API. Raises `EmptyIndex` if the store is empty. |
| `src/sage/api.py` | FastAPI app: `POST /ask {question, k?}` → `{answer, sources}`, `GET /health`. CORS is wide open (`allow_origins=["*"]`) — dev only. |
| `src/sage/ask.py` | Thin CLI over `service.answer`: `python -m sage.ask "question" [-k N]`. |
| `src/sage/models.py` | `Chunk` (incl. `make_id`), `ScoredChunk`, `Page`. |
| `src/sage/evals/` | RAGAS eval harness: `judge.py`, `dataset.py`, `harness.py` (config-driven variant runs), `scorecard.py`, `label_helper.py` / `build_ragset.py` (worksheet → hand-labeled eval set), `bench_judges.py`, `smoke.py`. |
| `evals/` | Eval data at the repo root (not under `src/`): candidate questions, the fillable labeling worksheet, and (once built) the hand-labeled `ragset_v1.jsonl`. See `evals/README.md` for the full workflow. |
| `data/qdrant/` | Local embedded Qdrant storage (gitignored). File-locked to one process. |
| `tests/` | pytest: `test_assembly.py`, `test_chunker.py`, `test_factory.py`. |

## Boundaries

- Nothing outside `src/sage/adapters/` may import a concrete backend SDK (Qdrant client,
  OpenRouter/httpx calls) directly — everything goes through the `ports.py` Protocols and
  the factory. This is the entire point of the port/adapter split.
- `service.py` is the one query-loop implementation; `ask.py` (CLI) and `api.py` (HTTP)
  are both thin wrappers over it — do not duplicate query logic into either.
- Ingestion (`ingest.py`) and the API (`api.py`) both open the Qdrant local-mode client,
  which is single-process/file-locked — they must not run concurrently.

## External dependencies

- **OpenRouter** — embeddings (`openai/text-embedding-3-small`, paid, ~$2e-7/query) and
  generation (currently a `:free` model, rate-limited/best-effort upstream). Needs
  `OPENROUTER_API_KEY`.
- **Qdrant** — embedded local mode (no server/Docker needed), data at `data/qdrant/`.
- **Groq / Gemini** (optional) — alternative judge-LLM providers for RAGAS evals, since
  OpenRouter's free tier is too rate-limited for eval runs (8 req/min).
- **Atlas** (`../atlas`, sibling repo) — Next.js UI that proxies to this API via
  `SAGE_API_URL`; not part of this repo.
