# Knowledge graph - design record

Updated: 2026-11-18 · Status: structural graph built in AuraDB from a frozen snapshot; `graph-local` and `text2cypher` built, not yet scored · Owner of open calls: Alp

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
| G9 | Same page snapshot for every arm? | Yes, freeze and rebuild | settled (Alp) |
| G10 | Which graph strategies, in what order? | local > text2cypher > entity > global | provisional |
| G11 | One graph or one per flavor? | One instance, separate namespaces | provisional |
| G12 | How is LLM-written Cypher kept safe? | Read session + write ban + limits | provisional |
| G13 | How does LLM extraction survive quotas? | Disk cache first, then load | provisional |
| G14 | Where does community detection run? | Decide when reached | open |
| G15 | Which questions prove each claim? | New labeled categories | open (Alp) |
| G16 | Which chunks does the graph hold? | The vector arm's own chunks | provisional |
| G17 | What does the `GraphStore` port expose? | Keyed merges + read-only Cypher | provisional |
| G18 | Where does a snapshot live? | Manifest in git, content local | provisional |
| G19 | What counts as a Symbol? | Identifier-shaped code spans, minus literals | provisional |
| G20 | How does `graph-local` rank what it reaches? | RRF of similarity and seed support | provisional |
| G21 | What does `text2cypher` hand the generator? | One excerpt: the query and its rows | provisional |
| G22 | How does `text2cypher` recover from a bad query? | One correction, then an honest miss | provisional |
| G23 | Which model writes the Cypher? | The generation model, settable | provisional |

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
Chosen: freeze and rebuild. Alp, 2026-11-16. Snapshot `langchain-2026-11-16` (192 pages,
id `3533e57389f9`); the vector collection of the same name (4,797 vectors) and the graph
are both built from it; the vector arms are re-scored on it.
Why: the old eval collection was ingested in July; a graph built from today's pages
would compete on a different corpus, which breaks invariant 3.
Rejected: accept the drift and lean on "source page retrieved".
Other path wins when: the corpus is immutable or versioned at the source, so a crawl
date already pins it.
Cost: every score dated before 2026-11-16 is on another corpus. `compare` now prints a
delta only for a row that shares the baseline's snapshot, generator and judge. Golden
question e011 is labeled with `langgraph/install.md`, which the site now redirects to
`langgraph/quickstart.md`, so its "source page retrieved" is always 0 until Alp relabels.

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
Built 2026-11-18 (`adapters/text2cypher.py`): comments, string literals and backticked
names are masked, then the query is refused if it holds a write or admin keyword
(CREATE, MERGE, SET, DELETE, DETACH, REMOVE, DROP, FOREACH, LOAD, USE, SHOW, ...), a query
option (EXPLAIN, PROFILE, CYPHER), a procedure `CALL` (subqueries `CALL () {}` pass),
`IN TRANSACTIONS`, or a second statement. It then runs as
`CALL () { <query> } RETURN * LIMIT n` (n = `SAGE_TEXT2CYPHER_MAX_ROWS`, default 50) in
the store's read session with its 20 s timeout. Checked live: the wrapper keeps the
inner `ORDER BY` and accepts `UNION`; `RETURN *` lists columns by name, not in the
inner order. A write the server refuses after the guard passed raises: that is a
guard bug, never a retry.

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

### G16 · Which chunks does the graph hold?
Chosen: the same `Chunker` as the vector arm, applied section by section. Verified
2026-11-16 on all 192 pages: the graph's chunk ids per page equal `chunker.chunk(page)`
(4,797 chunks), and a test pins it.
Why: with identical chunk texts a score difference is down to retrieval, not chunking.
It works because the recursive chunker splits at every `#` line start, a superset of
the real headings, so chunking each section gives the same pieces as chunking the page.
Rejected: one chunk per section (cleaner graph, but then "graph beats vector" could be
a chunking effect).
Other path wins when: chunking itself is the exhibit.

### G17 · What does the `GraphStore` port expose?
Chosen: `merge_nodes`, `merge_edges`, `prune`, `keys`, `ensure_*` for builders, and
`read(cypher, params)` for strategies. The adapter owns the write Cypher.
Why: builders can be tested for idempotence and pruning against an in-memory fake;
strategies still hand-write their Cypher (G3), and `read` is the single choke point
for G12.
Rejected: a bare `run(cypher)` port (every builder test would need a live Neo4j or
would only assert on query strings).
Other path wins when: there is a second graph database to support; then Cypher in
strategies leaks and the port must rise to named queries.

### G18 · Where does a snapshot live?
Chosen: manifest (url + sha256 per page, an id over all of them) committed in
`evals/snapshots/`; page content local in `data/snapshots/` (gitignored). Loading
verifies every hash and uses no network.
Why: the repo can prove which corpus a score used without redistributing the docs.
Rejected: commit the pages (4.7 MB of someone else's docs in a public repo); reuse the
mutable page cache (a rerun silently picks up new pages).
Other path wins when: the corpus is your own; then commit it.
Cost: lose `data/snapshots/` and the snapshot cannot be rebuilt once the site changes.

### G19 · What counts as a Symbol?
Chosen: an inline code span shaped like an identifier (dots and hyphens allowed, `()`
stripped, 3+ characters), minus language literals and primitive type names, plus the
last path segment of a `reference.langchain.com` link. Fenced code is ignored.
Result on the snapshot: 2,463 symbols, 6,088 mentions, 1,491 mentioned once; top hubs
`create_agent` (101 chunks), `create_deep_agent` (61), `interrupt` (57).
Why: prose backticks are the author saying "this is a named thing".
Rejected: identifiers from code blocks (every import line links everything).
Open consequence: hub symbols connect unrelated chunks, so `graph-local` must weight a
shared symbol by rarity (few mentions = strong link), not treat all alike.

### G20 · How does `graph-local` rank what it reaches?
Chosen: seed with the `graph_seed_k` (default 10, at least k) nearest chunks in Neo4j's
index; expand one hop: NEXT either way (weight 1.0), same section (0.7), the chunk most
similar to the question on each page linked to or from the seed's page (0.4), chunks
sharing a symbol (1/sqrt(chunks mentioning it)). A candidate's support is the sum over
seeds of seed similarity x its strongest edge weight. The seeds plus the 50
best-supported candidates are ranked twice, by similarity and by support, and fused with
the hand-written RRF. Code: `adapters/graph_local.py`.
Why: ranks need no calibration between a cosine and a support sum, and there is no
labeled multi-hop set to tune a weight on (G15). Ranking reached chunks by similarity
alone would just return the vector top-k again, so support has to count on its own.
Rejected: `similarity + lambda * support` (needs lambda tuned on labels); every chunk of
a linked page at equal weight (tried 2026-11-18: ties broke by chunk id and a raw
checkpoint dump reached the top 5; now one chunk per linked page); personalized
PageRank over several hops (HippoRAG style; needs GDS or the graph in process).
Other path wins when: there are enough labeled multi-hop questions to fit lambda, or the
bridging chunk sits two or more hops from any seed; then a tuned sum or PageRank pays.
This is not G1's fusion: both signals come from the graph store.

### G21 · What does `text2cypher` hand the generator?
Chosen: one excerpt holding the query and its rows: one numbered line per row,
`name: value` cells, vectors and build bookkeeping hidden even inside whole nodes, a
cell cut at 1,500 characters, the excerpt at 20,000. It names no page URL. `k` does not
apply; the row cap does (G12).
Why: a count or a list is one fact made of all its rows. Rows as k excerpts would cut
a list at k, and the assembly step ("edges" order) would reshuffle rows the query
sorted. The query is shown so the generator and the judge know what a number counts.
Rejected: one excerpt per row (cut at k, reordered); make the model return chunk ids
(loses aggregates, which are this strategy's whole claim, G10).
Cost: "source page retrieved" does not apply. The harness reports none, not a miss,
when an answer cites no page URL, although passage-style queries do carry
`source_url` in their rows (the labeled page appeared in the rows for 4 of the 5
multi-hop/hard questions, smoke run 2026-11-18). RAGAS context precision sees a single
context item, so it is all or nothing per question.
Other path wins when: the questions are passage lookups; then per-row excerpts with
their URLs score like the other arms (and `graph-local` is the better exhibit anyway).

### G22 · How does `text2cypher` recover from a bad query?
Chosen: two attempts. A query the guard refuses, the server rejects (syntax, unknown
name, timeout), or that matches no rows goes back to the model once with the reason. A
second empty result is served (nothing may really match); an earlier empty result beats
a correction that fails; a model that never writes a usable query yields an excerpt
saying so, which scores as a miss. Neo4j unreachable or every key at quota still raises.
Why: live on 2026-11-18, "which pages link to the LangGraph quickstart" first matched
the title against 'langgraph quickstart' and returned nothing (three pages are titled
"Quickstart"). The schema notes now say to match a product through the URL, and the
empty-result correction catches the next such miss. Raising on a model failure would
make the harness skip the question and retry it on every resume, so the failure would
never reach the score.
Rejected: no correction (one wrong name is a miss); unbounded retries (quota); vector
retrieval as a fallback (invariant 2).
Other path wins when: the honest answer is often "none" (audit questions such as
"which pages have no install section"); the empty-result correction then spends a call
and may loosen a correct query into a wrong one.

### G23 · Which model writes the Cypher?
Chosen: `SAGE_TEXT2CYPHER_MODEL`, defaulting to the generation model; the run header
and `index.jsonl` record it.
Why: invariant 3 fixes the generator and judge across arms; the Cypher writer is part
of the strategy, so it is a strategy knob. One free model keeps the first score cheap.
Rejected: a code-tuned model by default (a second quota to manage before any baseline).
Other path wins when: the scorecard shows the model's queries, not the graph, are the
weak point; then a stronger Cypher writer is the next variant.

## Invariants

1. Strategies are independent: each answers from its own store; none calls another or
   joins ids across stores. Enforced by: factory builds each strategy alone; a test runs
   every graph strategy with the vector store made to raise.
2. Every answer names the strategy that produced it; there is no silent fallback.
   Enforced by: `strategy` field on the answer and in `answers.jsonl`; a strategy whose
   store or model is unreachable raises. A model that cannot write a usable query is
   reported in the context as such, never replaced by another strategy's (G22).
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

`RetrievalStrategy.retrieve(question, k) -> list[ScoredChunk]` is the port (built
2026-11-15, `ports.py`); the dense/hybrid/rerank flow moved unchanged into the `vector`
strategy (`adapters/vector_strategy.py`), picked by `SAGE_STRATEGY`, and the generator
stays shared. `Answer.strategy`, the API response and `answers.jsonl` name the strategy;
evals pin `strategy=vector` unless a variant overrides it.

## Seams

| From -> To | Carrier | Contract | On failure |
|---|---|---|---|
| loader -> builders | `data/pages` on disk | `Page` (url, title, markdown) | builder reads what is cached |
| builder -> Neo4j | `GraphStore` write session | schema module | rerun; prune waits for success |
| strategy -> build | `sage/graph/current.py` `check_build` | Build node: snapshot, embedding model | `EmptyIndex` / `StaleGraph` |
| text2cypher -> LLM | `ChatModel.complete(system, user)` port | built from the generator registry (`make_chat_model`) | quota/unreachable raises |
| extractor -> loader | JSON cache on disk | entity record + provenance | resume from cache |
| service -> strategy | call | `retrieve(question, k)` | raise, named strategy |
| harness -> service | `Settings` override `strategy` | variant table | existing resume |

Dependency direction: builders and strategies depend on the schema module and the
`GraphStore` port, never on each other or on the Neo4j SDK; only the adapter imports
`neo4j`. Secrets (`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`) live in `.env`.

## Built (2026-11-16)

- AuraDB Free instance `29bd9238` (Neo4j 5.27-aura), created by Alp; the four
  `NEO4J_*` values are in `.env`. The database is named after the instance id, not
  `neo4j`.
- Structural graph, build `20261116T210907Z` from `langchain-2026-11-16`: 192 Page,
  2,534 Section, 4,797 Chunk (all embedded, `openai/text-embedding-3-small`, 1536
  dims), 2,463 Symbol, 1 Build; 19,143 relationships (MENTIONS 6,088, HAS_CHUNK 4,802,
  NEXT 4,657, HAS_SECTION 2,534, LINKS_TO 1,062). About 5% of the Free node cap. The
  first build took 2 min; a rebuild embeds nothing.
- `(:Build {namespace: 'Structural'})` records snapshot name, snapshot id and embedding
  model. A graph strategy should read it and refuse a snapshot other than its own.
- Checked live: `read()` rejects `CREATE`, `DETACH DELETE` and `CALL {} IN
  TRANSACTIONS` with `Neo.ClientError.Statement.AccessMode` (the server enforces it, so
  G12's read session holds on Aura Free); constraints and the vector index are
  idempotent; a wrong embedding dimension is refused. Aura creates the vector index
  with binary quantization by default.
- `graph-local` strategy (2026-11-18, G20) and its eval variant `graph-local`. It reads
  the Build node first and refuses a graph from another snapshot or embedding model.
  Seeds use Cypher 25 `SEARCH ... VECTOR INDEX` (the server marks
  `db.index.vector.queryNodes` deprecated); index scores equal
  `vector.similarity.cosine`, both in [0, 1]. Live: 1.5-4 s per question. Invariant 1's
  test exists (the vector store's factory raises). One real answer (m006) verified end
  to end. Retrieval-only smoke on the 5 multi-hop/hard questions, labeled pages in the
  top 5: baseline 4/11, graph-local 5/11 (m016 gains one). Anecdote, not a score.
- `text2cypher` strategy (2026-11-18, G12, G21-G23) and its eval variant `text2cypher`.
  The prompt's schema is built from `sage/graph/schema.py` plus a property table a test
  pins to what the builder writes. Live with `nvidia/nemotron-3.5-super-vl:free`:
  3-12 s per question (one 47 s outlier on the free model). Count, top-10, heading-tree,
  in-link, out-link and "pages without X" questions all gave valid queries; the in-link
  and out-link answers were checked against hand-written Cypher and match. One full
  `sage.ask` answer verified end to end. The 5 multi-hop/hard golden questions all ran
  without a refusal; on passage questions the model falls back to `CONTAINS` keyword
  search, which is where `graph-local` and the vector arms should win.
- Not built: a live-Neo4j test of a second build and of pruning (both are tested
  against the in-memory fake only).

## Open questions

1. Blocking claims: G15 labeling. Also e011's source URL (G9).
2. Settled 2026-11-16: Alp hand-writes none of the graph pieces ("build it all"); he
   reviews. The coaching protocol still applies to files that mark themselves as drills.
