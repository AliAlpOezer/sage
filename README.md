# sage

RAG over the LangChain docs, built from scratch as a learning project.
Every stage of the pipeline sits behind a swappable port:

```
INGESTION:  load docs -> chunk -> embed -> upsert to vector store
QUERY:      embed question -> top-k search -> assemble context -> generate answer
```

| Port          | Adapter #1 (default)                         | Planned         |
| ------------- | -------------------------------------------- | --------------- |
| `Embedder`    | OpenRouter (`openai/text-embedding-3-small`) | local (sbert)   |
| `VectorStore` | Qdrant (embedded local mode)                 | pgvector        |
| `Generator`   | OpenRouter (`nvidia/nemotron-3-super-120b-a12b:free`) | —       |

Backends are selected via `.env` (see `.env.example`) — the factory in
`src/sage/factory.py` resolves names to registered adapters.

## Setup

```sh
uv sync
cp .env.example .env   # add your OPENROUTER_API_KEY
uv run python -m pytest
```

## Build the index

Ingestion is idempotent *per chunk*: a chunk id is `sha256(source_url + text)`, so
re-running upserts each chunk in place rather than duplicating it. Re-running
against an **unchanged** corpus reproduces the same vector count.

```sh
uv run python -m sage.ingest                     # ~185 pages, ~$0.03
```

A run prints one line per stage and ends with the stored count:

```
index lists 185 pages under https://docs.langchain.com/oss/python/
fetched 185 pages
chunked into 4842 chunks
embedded 4842 chunks (dimension 1536)
store now holds 4893 vectors
```

> Embedded qdrant allows one process at a time. **Stop the API server before
> (re)ingesting** — otherwise you'll hit `already accessed by another instance`.

Exact counts track the live docs and drift over time. Note ingest **adds and
overwrites but never deletes**: when a page's text changes, its old chunks keep
their old ids and linger as orphans, so the stored count can exceed the chunks
just embedded (above, 4893 > 4842). For a clean rebuild, delete `data/qdrant/`
first, then re-run.

## Query (CLI)

```sh
uv run python -m sage.ask "How do I use create_agent?"
uv run python -m sage.ask -k 8 "..."             # override top-k
```

Answers cite numbered sources; `[n]` in the answer maps to the printed source list.

## Serve the API + UI

The same query loop is exposed over HTTP for the [Atlas](../atlas) UI:

```sh
uv run python -m uvicorn sage.api:app --port 8000
```

> On Windows run it as `python -m uvicorn` (shown above), **not** `uv run uvicorn …`
> — the bare-console-script form fails with `os error 5` on some setups.

Endpoints: `POST /ask {question, k?}` → `{answer, sources[]}`, and `GET /health`.

The UI (Next.js, in `../atlas`) proxies to this server via `SAGE_API_URL`
(default `http://localhost:8000`), keeping the API key server-side. With the
Sage API running:

```sh
cd ../atlas && pnpm install && pnpm dev          # open http://localhost:3000/ask
```

Operational handoff: `docs/context/sage.md`. Deep knowledge base (every
decision with alternatives & trade-offs): `docs/wiki/index.md`.
