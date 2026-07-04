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
| `Generator`   | OpenRouter (`anthropic/claude-sonnet-4-6`)   | —               |

Backends are selected via `.env` (see `.env.example`) — the factory in
`src/sage/factory.py` resolves names to registered adapters.

## Setup

```sh
uv sync
cp .env.example .env   # add your OPENROUTER_API_KEY
uv run python -m pytest
```

## Usage

```sh
uv run python -m sage.ingest                     # build the index (idempotent, ~$0.03)
uv run python -m sage.ask "How do I use create_agent?"
uv run python -m sage.ask -k 8 "..."             # override top-k
```

Answers cite numbered sources; `[n]` in the answer maps to the printed source list.

Operational handoff: `docs/context/sage.md`. Deep knowledge base (every
decision with alternatives & trade-offs): `docs/wiki/index.md`.
