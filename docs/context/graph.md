# Knowledge graph - design record

Updated: 2026-11-15 · Status: design, nothing built · Owner of open calls: Alp

Self-contained: everything needed for graph work is in this file.

## What this is for

Show, with scores, which kinds of question a knowledge graph answers better than vector
retrieval, and which it does not. Each retrieval strategy is a standalone exhibit with a
stated "this wins when" claim.

Stays true if every technology changes: the strategies are independent and comparable
under the same conditions. Every fork in their design is written down here as a decision
node, so the path taken, and why, can be learned from.

## Decision nodes

Each node: the question, the path chosen, why, what was rejected, and **when the other
path would win**. That last line is the portfolio material. Status: `settled` (Alp
decided or evidence exists), `provisional` (my call, open to Alp), `open` (waiting).

| ID | Fork | Chosen | Status |
|---|---|---|---|
| G1 | Fuse the graph into RRF, or keep strategies separate? | Separate exhibits | settled (Alp) |
| G2 | Which graph store? | Neo4j AuraDB Free | settled |
| G3 | Library or hand-built? | Hand-written Cypher, official driver | settled |
| G4 | Build the graph from what? | The page snapshot, not Qdrant | provisional |
| G5 | How does a graph query find its starting nodes? | Neo4j's own vector index | provisional |
| G6 | Structure-derived or LLM-extracted graph first? | Structure first, LLM second | settled (STATUS) |
| G7 | Structural schema granularity | Page > Section > Chunk, + Symbol | provisional |
| G8 | Which corpus? | LangChain only, first | provisional |
| G9 | Same page snapshot for every arm? | Yes, freeze and rebuild | open (Alp) |
| G10 | Which graph strategies, in what order? | local > text2cypher > entity > global | provisional |
| G11 | One graph or one per flavor? | One instance, separate namespaces | provisional |
| G12 | How is LLM-written Cypher kept safe? | Read session + write ban + limits | provisional |
| G13 | How does LLM extraction survive quotas? | Disk cache first, then load | provisional |
| G14 | Where does community detection run? | Decide when reached | open |
| G15 | Which questions prove each claim? | New labeled categories | open (Alp) |

### G1 · Fuse the graph into RRF, or keep strategies separate?
Chosen: separate. Each strategy (vector, hybrid, hybrid+rerank, each graph strategy) runs
alone and is scored alone. Alp, 2026-11-15.
Why: a fused win cannot be attributed, so the portfolio could not say *when* a graph
helps. Rejected: graph as a third RRF list (the 2026-11-09 plan).
Other path wins when: you ship one production answer box and want the best single
score; then fusion or a question router is a later exhibit built on these results.

### G2 · Which graph store?
Chosen: Neo4j AuraDB Free (checked 2026-11-15: 200k nodes, 400k relationships, vector
indexes, pauses after 3 days idle; graph algorithms only via an Aura Graph Analytics
session: 1 at a time, 2 GB, 4 h max).
Why: Cypher is the thing worth learning and showing; the Neo4j docs are already in the
corpus. Rejected: local Neo4j (3.6 GB RAM, Docker off); networkx in process (no query
language, so no text2cypher exhibit, rebuilt every process); Kuzu embedded (I recall
upstream archived it in 2025; unverified).
Other path wins when: the graph is small, read-only and lives inside one Python
process; networkx is then simpler than any server.
Cost: the instance pauses when idle and must be resumed in the console.

### G3 · Library or hand-built?
Chosen: hand-written Cypher over the official `neo4j` driver, behind a port.
Why: the 2026-07-04 "no RAG framework" decision applies; the queries are the lesson.
Rejected: `neo4j-graphrag-python` (`SimpleKGPipeline`, ready retrievers).
Other path wins when: time to a working demo matters more than understanding; it can
return later as a "library vs hand-built" exhibit.

### G4 · Build the graph from what?
Chosen: the page snapshot (loader + `data/pages` cache), parsed from raw markdown.
Why: headings and links survive only in raw markdown; Qdrant payloads are flat chunks.
Reading Qdrant would also tie the graph to the vector store (breaks invariant 1).
Rejected: scroll chunks out of Qdrant. Cost: pages must be fetched again (82 cached).
Other path wins when: the source is gone and the vector store is the only copy.

### G5 · How does a graph query find its starting nodes?
Chosen: a vector index inside Neo4j on Chunk embeddings, filled at build time through the
existing `Embedder` port (same model, cents to re-embed).
Why: keeps the graph strategies free of Qdrant, so a graph win is the graph's.
Rejected: seed from Qdrant hits then hop into Neo4j (couples the two stores, and the win
becomes half Qdrant's); full-text index only (misses paraphrases, but it is free and
could be its own variant).
Other path wins when: one production system already holds the vectors and duplicating
them is a real cost.

### G6 · Structure-derived or LLM-extracted graph first?
Chosen: structure first (links, heading tree, code-symbol mentions; zero LLM cost,
deterministic), LLM entity extraction second as the paid comparison.
Why: the cheap graph is the baseline that tells whether paying for extraction helps.
Other path wins when: the corpus has no structure (tickets, emails, transcripts); then
only extraction yields a graph.

### G7 · Structural schema granularity
Chosen: `(:Page)-[:HAS_SECTION]->(:Section)-[:HAS_SECTION]->(:Section)`,
`(:Section)-[:HAS_CHUNK]->(:Chunk)`, `(:Chunk)-[:NEXT]->(:Chunk)`,
`(:Page)-[:LINKS_TO]->(:Page)`, `(:Chunk)-[:MENTIONS]->(:Symbol)`. A Symbol is a
backticked identifier or API-reference link target, e.g. `ChatOpenAI`.
Rejected: pages only (one hop drags in whole pages); chunks with similarity edges
(k-NN edges repeat what vector search already knows).
Other path wins when: pages are short and single-topic; page-level is then enough.

### G8 · Which corpus?
Chosen: LangChain only (the eval corpus), extend to the other five sites after.
Why: only LangChain has golden questions, so only there can a claim be scored. All six
sites would fit the node cap, but LLM extraction over ~24k chunks at 1,000 free requests
per day takes weeks.
Other path wins when: the demo is breadth (cross-site questions), not a scored claim.

### G9 · Same page snapshot for every arm?
Recommended: freeze one LangChain snapshot, rebuild the `langchain-docs` collection and
the graph from it, re-score the vector arms. The eval collection was ingested in July;
a graph built from today's pages would compete on a different corpus, which breaks
invariant 3. Cost: one re-ingest (cents) and about a day of free judge quota.
Rejected: accept the drift and lean on "source page retrieved".

### G10 · Which graph strategies, in what order?
Each targets a question type vector retrieval is bad at:

| Strategy | How | Should win on | Build cost |
|---|---|---|---|
| `graph-local` | vector seed, expand via section, NEXT, LINKS_TO, shared Symbol | multi-hop across linked pages | none |
| `text2cypher` | LLM writes a read query over the schema | aggregate / list / count ("which X support Y") | none |
| `graph-entity` | same as local, over LLM-extracted entities | relations the docs never link | 1 LLM call per chunk |
| `graph-global` | community summaries (Leiden) | "what is this corpus about" | clustering + summaries |

Order is cheapest-first. Rejected now: a router that picks a strategy per question (it is
the fusion exhibit of G1, built last).

### G11 · One graph or one per flavor?
Chosen: one AuraDB instance (Free allows one), structural and extracted graphs in
separate label namespaces that no query crosses. Rejected: merging extracted entities
into the structural graph (a win could not be attributed to either).
Other path wins when: in production you want both edge types in one traversal.

### G12 · How is LLM-written Cypher kept safe?
Chosen: run it only in a read-access session, reject any write clause before sending,
force a `LIMIT`, set a timeout. Rejected: trust the prompt. Cost: a few legitimate
queries get refused.

### G13 · How does LLM extraction survive quotas?
Chosen: extraction writes JSON to a disk cache keyed by (chunk hash, model, prompt
version), a separate step loads the cache into Neo4j. Same pattern as resumable
scoring. Rejected: extract-and-write in one pass (a quota stop mid-run leaves a
half graph you cannot tell from a full one).

### G14 · Where does community detection run? (open, decide at `graph-global`)
Options: an Aura Graph Analytics session (free, 2 GB, 4 h) or local `igraph`/`leidenalg`
on the exported edge list (no session limits; the graph is small).

### G15 · Which questions prove each claim? (open, Alp)
The golden set has 4 multi-hop and no aggregate or global questions, so G10's "should
win on" column cannot be scored yet. Needs about 20 multi-hop, 10 aggregate, 5 global,
labeled by Alp (labeling is never delegated). Blocks claims, not building.

## Invariants

1. Strategies are independent: each answers from its own store; none calls another or
   joins ids across stores. Enforced by: factory builds each strategy alone; a test runs
   every graph strategy with the vector store made to raise.
2. Every answer names the strategy that produced it; there is no silent fallback.
   Enforced by: `strategy` field on the answer and in `answers.jsonl`; a failing
   strategy raises.
3. No "X beats Y" without the same page snapshot, generator and judge. Enforced by:
   `compare.md` shows all three per row (snapshot column is new).
4. The graph is derived and rebuildable: built only from the snapshot by keyed `MERGE`,
   nodes from an older build pruned after a successful build, never hand-edited.
   Enforced by: uniqueness constraints, `build_id` prune, a test that two builds match.
5. Every LLM-derived node and edge carries provenance (chunk id, model, prompt version).
   Enforced by: the loader refuses records without it.
6. LLM-written Cypher can never write. Enforced by: G12, tested.
7. Every fork gets a decision node here before code that depends on it merges.
   Enforced by: PR review (process, not code).

## Components

| Component | Owns | Autonomy | Fails how |
|---|---|---|---|
| Page snapshot (`loader`, `data/pages`) | raw markdown per URL | autonomous | site refuses: stops, resumes from cache |
| Graph schema (`sage/graph/schema.py`) | labels, keys, constraints, namespaces | - | - |
| `GraphStore` port + Neo4j adapter | driver, read/write sessions | - | paused instance: clear "resume in console" error |
| Structural builder | markdown -> nodes/edges, embeddings | autonomous, idempotent | partial build: rerun converges, prune only after success |
| Extractor (LLM) | chunk -> entities JSON in cache | autonomous, resumable | quota: stops; bad JSON: marked failed, retried |
| Extraction loader | cache -> extracted namespace | autonomous, idempotent | missing provenance: refused |
| Strategies (`RetrievalStrategy` port) | question -> context | autonomous, read-only | store down: raises, no fallback |
| Eval harness | scores per strategy | autonomous, resumable | existing |

`RetrievalStrategy.retrieve(question, k) -> list[ScoredChunk]` is the new port; today's
dense/hybrid/rerank flow in `service.answer` becomes the `vector` strategy unchanged, and
the generator stays shared.

## Seams

| From -> To | Carrier | Contract | On failure |
|---|---|---|---|
| loader -> builders | `data/pages` on disk | `Page` (url, title, markdown) | builder reads what is cached |
| builder -> Neo4j | `GraphStore` write session | schema module | rerun; prune waits for success |
| extractor -> loader | JSON cache on disk | entity record + provenance | resume from cache |
| service -> strategy | call | `retrieve(question, k)` | raise, named strategy |
| harness -> service | `Settings` override `strategy` | variant table | existing resume |

Dependency direction: builders and strategies depend on the schema module and the
`GraphStore` port, never on each other or on the Neo4j SDK; only the adapter imports
`neo4j`. Secrets (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`) live in `.env`.

## Open questions

1. Blocking build: Alp creates the AuraDB Free instance and puts the three `NEO4J_*`
   values in `.env`.
2. Blocking claims: G15 labeling.
3. Carried: G9 snapshot rebuild (recommended yes).
4. Carried: which pieces Alp hand-writes as drills. Candidates: the `graph-local`
   expansion Cypher, the markdown section parser, the text2cypher guard.
