# sage

Ask a question about the LangChain docs and get an answer that cites the pages it came from.

sage is a retrieval-augmented generation (RAG) system built from scratch as a learning
project. It does not use LangChain or LlamaIndex to do the RAG part: chunking, embedding,
search, fusion, reranking, context assembly and the knowledge graph are all hand-written,
so every step is visible and can be measured on its own.

**Highlights**

- **Hybrid search**: dense vectors in Qdrant plus BM25 keyword search, merged with a
  hand-written Reciprocal Rank Fusion (RRF).
- **Reranking**: a Cohere cross-encoder re-scores the candidates; the biggest single
  gain in the evals (context precision 0.66 to 0.90).
- **Knowledge graph on Neo4j**: the docs' structure (pages, headings, passages, links,
  code symbols) as a graph, searched with one-hop expansion (`graph-local`) or with
  LLM-written Cypher queries (`text2cypher`, GraphRAG style).
- **Evaluated with RAGAS**: 36 hand-labeled questions, faithfulness, relevancy,
  precision and recall per variant, plus a check that sage declines what the docs
  cannot answer.
- **Six doc sites**: LangChain, Langfuse, Qdrant, Neo4j, neo4j-graphrag and RAGAS.
- **Ports and adapters**: every stage is swappable from `.env`, served over a CLI and a
  FastAPI endpoint.

```text
$ uv run python -m sage.ask "How do I add memory to an agent?"

The approach depends on which agent framework you are using.

LangGraph / langchain agents (create_agent):
- Short-term memory is managed as part of the agent's state [2].
- Long-term memory is added by creating a store and passing it to
  create_agent via store= [1] ...

Sources:
  [1] Long-term memory - https://docs.langchain.com/oss/python/langchain/long-term-memory.md  (score 0.804)
  [2] Memory - https://docs.langchain.com/oss/python/langgraph/add-memory.md  (score 0.719)
  ...
```

## How it works

There are two pipelines. Ingestion runs once to build the index; the query pipeline runs
for every question.

```text
INGESTION   doc sites ──> fetch pages ──> chunk ──> embed ──> vector store (Qdrant)
                                     └──> structure ──> knowledge graph (Neo4j)

QUERY       question ──> retrieval strategy ──> arrange context ──> LLM ──> cited answer
```

Every stage sits behind a small interface (a Python `Protocol`, called a *port*) in
[`src/sage/ports.py`](src/sage/ports.py). Each concrete backend is an *adapter* in
[`src/sage/adapters/`](src/sage/adapters/) that registers itself under a name. You pick
the adapters in `.env`, so swapping a backend means writing one adapter, not editing the
pipeline.

| Port                | What it does                              | Adapters                                  |
| ------------------- | ----------------------------------------- | ----------------------------------------- |
| `Chunker`           | Splits a page into passages               | `recursive`, `fixed`, `structural`, `contextual` |
| `Embedder`          | Turns text into vectors                   | `openrouter` (`openai/text-embedding-3-small`) |
| `VectorStore`       | Stores vectors, finds the nearest ones    | `qdrant` (embedded on disk, or Qdrant Cloud) |
| `SparseRetriever`   | Keyword search                            | `bm25`                                    |
| `Reranker`          | Re-scores candidates with a cross-encoder | `cohere`, `bge`                           |
| `GraphStore`        | Reads and writes the knowledge graph      | `neo4j` (AuraDB Free)                     |
| `RetrievalStrategy` | Turns a question into ranked passages     | `vector`, `graph-local`, `text2cypher`    |
| `Generator`         | Writes the answer                         | `openrouter`, `omniroute`                 |

## Retrieval strategies

The interesting part of the project is comparing different ways to find the right
passages. Each strategy stands on its own and is selected with `SAGE_STRATEGY`.

- **`vector`** (default). Dense search in Qdrant. Optionally adds BM25 keyword search,
  merges both lists with Reciprocal Rank Fusion (RRF), and reranks the result with Cohere.
  This is what the app serves today: hybrid search plus reranking.
- **`graph-local`**. Starts from the passages closest to the question, then walks one hop
  through the knowledge graph: neighbouring passages, the rest of the section, linked
  pages, and passages that mention the same API symbol. A passage that several good
  starting points lead to ranks higher, which is what a question spanning two pages needs.
- **`text2cypher`**. An LLM writes a Cypher query against the graph. A guard rejects
  anything that writes, the query runs read-only with a row cap, and one retry fixes
  errors. Built for counting and listing questions ("which pages mention X?"), not for
  explaining a concept.

The knowledge graph is built from the structure of the docs, with no LLM calls: pages,
their heading tree, passages, links between pages, and the code symbols each passage
mentions. Every design choice and its rejected alternatives are written down in
[`docs/context/graph.md`](docs/context/graph.md).

## Results

Every retrieval change is scored against a hand-labeled set of 36 questions
([`evals/ragset_v1.jsonl`](evals/ragset_v1.jsonl)): 22 the docs can answer and 14 they
cannot. Answers are scored with [RAGAS](https://docs.ragas.io/); the unanswerable ones
are scored by whether sage declined to answer.

| Variant        | Faithfulness | Answer relevancy | Context precision | Context recall | Right page in top 5 |
| -------------- | -----------: | ---------------: | ----------------: | -------------: | ------------------: |
| baseline       | 0.967        | 0.781            | 0.656             | 0.720          | 0.773               |
| hybrid         | 0.951        | 0.734            | 0.797             | 0.735          | 0.727               |
| rerank-cohere  | 0.961        | 0.723            | **0.896**         | 0.759          | 0.773               |
| hybrid-rerank  | 0.891        | 0.708            | 0.842             | **0.800**      | **0.818**           |

All four declined all 14 unanswerable questions. Reranking gives the clearest gain
(context precision +0.24). With only 22 answerable questions, differences under about
0.05 are noise. Full table: [`evals/runs/compare.md`](evals/runs/compare.md).

These scores come from a July 2026 crawl. The evals have since moved to a frozen
snapshot of the docs so that every strategy, including the graph ones, is scored on the
exact same pages; the re-run is pending.

## Getting started

You need [uv](https://docs.astral.sh/uv/) and an [OpenRouter](https://openrouter.ai/) API
key with a little credit (embedding all LangChain docs costs about $0.03; the default
generator is a free model).

```sh
git clone https://github.com/AliAlpOezer/sage.git
cd sage
uv sync
cp .env.example .env          # then set OPENROUTER_API_KEY_1 and SAGE_GENERATOR=openrouter
uv run python -m pytest
```

### 1. Build the index

```sh
uv run python -m sage.ingest
```

This reads each doc site's sitemap, fetches every page as markdown, chunks, embeds and
stores the passages. It prints one line per stage and ends with the number of vectors
stored. Re-running is safe: a passage's id is a hash of its URL and text, so unchanged
passages are overwritten in place, not duplicated.

By default only the LangChain docs are indexed. `SAGE_SOURCES` adds more sites:
`langchain`, `langfuse`, `qdrant`, `neo4j`, `neo4j-graphrag`, `ragas`.

### 2. Ask a question

```sh
uv run python -m sage.ask "How do I use create_agent?"
uv run python -m sage.ask -k 8 "..."     # use 8 passages instead of 5
```

`[n]` in the answer refers to the numbered source list printed under it.

### 3. Or run it as an API

```sh
uv run python -m uvicorn sage.api:app --port 8000
```

- `POST /ask` with `{"question": "...", "k": 5}` returns `{answer, sources}`
- `GET /health`

On Windows use `python -m uvicorn` as shown; `uv run uvicorn ...` fails on some setups.

> The embedded Qdrant store allows one process at a time. Stop the API server before
> you re-ingest, or you will see `already accessed by another instance`.

### Optional: the knowledge graph

The graph strategies need a Neo4j database; the free tier of
[Neo4j AuraDB](https://neo4j.com/product/auradb/) is enough. Put its credentials in
`.env` (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`), then:

```sh
uv run python -m sage.snapshot freeze langchain-2026-11-16 --sources langchain
SAGE_SNAPSHOT=langchain-2026-11-16 uv run python -m sage.graph.build
SAGE_STRATEGY=graph-local uv run python -m sage.ask "..."
```

A snapshot freezes the crawled pages on disk, so the vector index and the graph are
built from exactly the same text. The graph refuses to answer if it was built from a
different snapshot or embedding model.

## Configuration

All settings live in `.env`. [`.env.example`](.env.example) lists every one with its
default and a short explanation. The ones you are most likely to change:

| Variable               | Default          | Meaning                                           |
| ---------------------- | ---------------- | ------------------------------------------------- |
| `OPENROUTER_API_KEY_1` | (required)       | More keys (`_2`, `_3`, ...) rotate on rate limits |
| `SAGE_GENERATOR`       | `omniroute`      | `openrouter`, or a local OmniRoute gateway        |
| `SAGE_STRATEGY`        | `vector`         | `vector`, `graph-local`, `text2cypher`            |
| `SAGE_SPARSE_RETRIEVER`| `none`           | `bm25` turns on hybrid search                     |
| `SAGE_RERANKER`        | `none`           | `cohere` (needs `COHERE_API_KEY`)                 |
| `SAGE_SOURCES`         | `langchain`      | Comma-separated doc sites to index                |
| `SAGE_QDRANT_URL`      | (empty)          | Use Qdrant Cloud instead of the local store       |
| `SAGE_TOP_K`           | `5`              | Passages given to the LLM                         |

## Running the evals

The eval harness runs a named variant end to end: generate an answer for each of the
36 questions, score them, write a scorecard. It resumes where it stopped, which matters
on free-tier rate limits.

```sh
uv sync --group eval
uv run python -m sage.evals.harness run rerank-cohere
uv run python -m sage.evals.harness compare      # rebuilds evals/runs/compare.md
```

How the question set was built and labeled: [`evals/README.md`](evals/README.md).

## Project layout

```text
src/sage/
  ports.py          the interfaces every stage implements
  adapters/         one module per backend (Qdrant, OpenRouter, BM25, Cohere, Neo4j, strategies)
  factory.py        turns names from .env into adapter instances
  config.py         every setting, read from .env
  sources.py        the doc sites sage can index
  loader.py         sitemap crawl and page fetch
  ingest.py         ingestion pipeline        (python -m sage.ingest)
  service.py        the one query loop, shared by CLI and API
  assembly.py       orders passages in the prompt (best ones at the edges)
  ask.py, api.py    CLI and HTTP front ends
  snapshot.py       frozen page snapshots     (python -m sage.snapshot)
  graph/            graph schema, markdown parser, graph builder
  evals/            RAGAS harness, abstention check, scorecards
evals/              question set, eval runs, snapshot manifests
docs/context/       short design notes: architecture, decisions, gotchas, graph
docs/wiki/          longer explainers and every decision with its trade-offs
tests/              pytest suite, runs offline
```

## Design notes

- [`docs/context/architecture.md`](docs/context/architecture.md): where everything lives and how a query flows.
- [`docs/context/decisions.md`](docs/context/decisions.md): why each library, model and backend was chosen.
- [`docs/context/graph.md`](docs/context/graph.md): the knowledge graph design, decision by decision.
- [`docs/context/gotchas.md`](docs/context/gotchas.md): things that broke and why.
- [`docs/context/STATUS.md`](docs/context/STATUS.md): what is done and what is next.

A separate Next.js front end, Atlas, talks to the API through `POST /ask`; it lives in
its own repository.

## Tech stack

Python 3.12, uv, FastAPI, Qdrant, Neo4j, OpenRouter, Cohere Rerank, rank-bm25, RAGAS,
pytest, ruff.
