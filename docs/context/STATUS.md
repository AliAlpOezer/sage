# Status - sage

Last updated: 2026-11-18

## Current focus

Turning sage into a showcase (decided 2026-11-09): hybrid retrieval (BM25 sparse + HNSW
dense in Qdrant) plus GraphRAG on Neo4j, fused with the hand-written RRF. **Cloudflare
hosting is deferred**: develop locally, free services only. First unblock evals, since
every retrieval change has to be scored to count.

Alp, 2026-11-10: tired of the project stalling on the baseline score since August. Evals
run in the background and must not block feature work. Same day he decided the corpus
grows to four doc sites (LangChain, Langfuse, Qdrant, Neo4j).

Alp, 2026-11-15: keep hybrid and rerank (the app now serves both, see `decisions.md`);
W6 merged to master. Next is the knowledge-graph design. Framing: a portfolio of
retrieval strategies that need not interact or be fused; each is shown on its own with
when it pays off. Every design fork is recorded with the chosen path and why, as a
learning trail.

## State (verified 2026-11-09)

- Golden set `evals/ragset_v1.jsonl` is done: 36 hand-labeled triples (17 easy,
  14 unanswerable, 4 multi-hop, 1 hard). Empty `source_urls` on u001-u014 is correct.
- The July-August W6 work (reranker port, BM25 + RRF hybrid, contextual retrieval,
  OmniRoute generator) and the 2026-11-09 OpenRouter key rotation are committed on
  branch `w6-hybrid-rerank-contextual` (2026-11-09; not pushed, not merged; it also
  carries the 4 unmerged commits of `add-context-pack`). 34 tests pass, ruff clean.
  Still to do: a separate repo-wide `ruff format` commit (23 of 36 files do not match
  the global ruff config; the repo has no `[tool.ruff]`).
- Multi-source corpus (2026-11-10, uncommitted on this branch): `src/sage/sources.py`
  registry + per-source loader + batched ingest (512 chunks per round). Collection
  `tech-docs` holds 19,401 vectors from all 1,106 pages (192 LangChain incl. 37 LangGraph,
  326 Langfuse, 360 Qdrant, 228 Neo4j). The harness pins evals to the frozen
  `langchain-docs` collection (`EVAL_CORPUS`). 49 tests pass, ruff clean. Verified with a
  real `sage.ask` question per new site. No golden questions exist for the three new
  sites. The collection sits at embedded Qdrant's ~20k-point comfort limit: more sources
  (candidates offered to Alp: neo4j-graphrag-python, Neo4j GDS, RAGAS, OpenRouter; no
  pick yet) need the Qdrant server/cloud move first.
- OpenRouter is the working route (2026-11-09): `$10` credit bought on the account of
  `OPENROUTER_API_KEY_2` (total_credits 10, so 1,000 free-model requests/day). `.env` has
  `SAGE_GENERATOR=openrouter`, `SAGE_JUDGE_PROVIDER=openrouter`, the nemotron judge model,
  `SAGE_COLLECTION=tech-docs` and all four `SAGE_SOURCES` (set 2026-11-10; on 2026-11-09
  the file had silently gone back to omniroute, see `gotchas.md`). Paid query embeddings
  402 on the other keys and rotate to key 2 (own `embeddings` key pointer); chat calls use
  `:free` models and walk keys 1..8, so credit is only spent on embeddings (cents).
  Verified with a real `sage.ask` question end to end.
- Superseded by the 2026-11-15 evals below. Hybrid vs baseline, same judge (`nvidia/nemotron-3.5-super-vl:free`, 2026-11-10, n=36,
  `evals/runs/compare.md`): baseline faithfulness 0.849, answer_relevancy 0.610,
  context_precision 0.501, context_recall 0.611; hybrid 0.887 / 0.537 / 0.501 / 0.630.
  Retrieval is a tie (precision equal, recall +0.019 is noise at n=36), so BM25 + RRF
  shows no measurable gain on this set. The two generation metrics are not attributable
  to retrieval: the cached answers came from different generators (hybrid 2026-08-04,
  baseline 2026-08-12) and `answers.jsonl` does not record which. One baseline sample has
  no faithfulness/relevancy score. The judge needs `SAGE_JUDGE_MAX_TOKENS=16000`: at
  4000 it truncated 20 calls in one pass (not yet in `.env`).

- Why the means look poor (2026-11-10, per-category from `details.csv`): the 14 unanswerable
  questions score answer_relevancy ~0.26, precision ~0.15, recall ~0.41 by construction
  (RAGAS rates a correct refusal as irrelevant; there is no context to find). Answerable
  only (n=22): baseline 0.864 / 0.841 / 0.720 / 0.727, hybrid 0.971 / 0.722 / 0.727 / 0.780.
  Real defects: baseline e030 answer is `<unk>` garbage from the free generator; baseline
  e001, e024, e027 have zero context recall. Open: score unanswerables with an
  abstention check instead of RAGAS, record the generator model in `answers.jsonl`,
  regenerate both arms with one generator.
- Qdrant Cloud move (Alp 2026-11-10: yes if free; OpenRouter docs not wanted): free tier
  is 1 GB RAM / 4 GB disk, no card, suspended after 1 week unused, deleted after 4 weeks
  inactive (Qdrant docs, checked 2026-11-10). Code is ready: `SAGE_QDRANT_URL` +
  `QDRANT_API_KEY` switch `QdrantStore` to a remote cluster; evals stay on the local
  store. Waiting on Alp to create the cluster. Then add neo4j-graphrag-python, Neo4j GDS
  and RAGAS docs as sources (their markdown access is unprobed).

- Authorized by Alp 2026-11-10 ("do all those suggestions", and do his side via Chrome
  where possible): (1) score unanswerables by abstention check, RAGAS on answerable only;
  (2) record generator model in `answers.jsonl`, regenerate baseline + hybrid with one
  generator; (3) score `rerank-cohere`; (4) inspect zero-recall e001/e024/e027 by hand;
  (5) create the free Qdrant Cloud cluster, put `SAGE_QDRANT_URL`/`QDRANT_API_KEY` in
  `.env`, re-ingest there; (6) add neo4j-graphrag-python, Neo4j GDS, RAGAS docs. Labeling
  more questions stays Alp's. Nothing committed yet; commits were not requested.

- State 2026-11-10 ~16:30 local, all uncommitted on this branch:
  - Harness: unanswerables scored by abstention (`evals/abstention.py`), RAGAS means on
    answerable only, judge-free `source page retrieved` line, `generator` recorded in
    `answers.jsonl`, scores bound to the answer by hash, `SAGE_JUDGE_MAX_TOKENS=16000`.
  - baseline, hybrid, rerank-cohere each have 36 answers from
    `nvidia/nemotron-3.5-super-vl:free`. Scoring was started in the background (log:
    session scratchpad `evals4.log`); if it died, resume per variant with
    `uv run python -m sage.evals.harness run <variant> --phase score`, then `compare`.
    Free-model quota (resets 00:00 UTC) may run out mid-way; the phase resumes.
  - Labeled source page in top 5 (answerable n=22): baseline 17, hybrid 16,
    rerank-cohere 17. Missed by all three: e002, e005, h002 (check labels/chunking).
  - Corpus in the cluster (page counts checked 2026-11-10): 24,218 vectors, 1,361 pages:
    LangChain 192, Langfuse 326, Qdrant 360, RAGAS 133 (11 of 144 have no `/index.md`),
    Neo4j Cypher 162, getting-started 42, Python driver 14, GenAI plugin 10, GraphRAG
    package 7 (all complete), Graph Data Science 115 of 189. Only GDS is incomplete:
    Neo4j's request budget (see `gotchas.md`) lets about 75 pages through per run now.
    The loader caches pages in `data/pages` and stops at a sustained refusal, so repeat
    `SAGE_SOURCES=neo4j uv run python -m sage.ingest` a few times, spaced apart, until it
    reports 417 of 417. `.env` `SAGE_SOURCES` lists all six sources. 55 tests pass.
  - Qdrant Cloud is live (2026-11-10): Alp created a free AWS cluster; `.env` has
    `SAGE_QDRANT_URL` + `QDRANT_API_KEY` (he first saved them as `QDRANT_API_ENDPOINT` /
    `QDRANT_SECRET`; renamed). The local `tech-docs` collection was copied point for
    point (24,216 vectors, no re-embedding) and retrieval against the cluster verified.
    The app and `sage.ingest` now use the cluster; evals still use local `langchain-docs`.
    `qdrant-client` upgraded 1.18 -> 1.20 to match the server (`uv.lock`). Free clusters
    suspend after 1 week unused and are deleted after 4 weeks inactive.
  - Evals complete 2026-11-15 (`evals/runs/compare.md`), one generator and judge
    (nemotron free), answerable n=22, faithfulness / answer_relevancy /
    context_precision / context_recall / source page in top 5:
    baseline 0.967 / 0.781 / 0.656 / 0.720 / 0.773;
    hybrid 0.951 / 0.734 / 0.797 / 0.735 / 0.727;
    rerank-cohere 0.961 / 0.723 / 0.896 / 0.759 / 0.773. All three declined 14/14
    unanswerable. Reranking gives the clearest gain (precision +0.240); hybrid +0.141
    precision but finds the labeled page less often. n=22, so treat deltas under ~0.05
    as noise. Answer relevancy drops on both arms; not yet inspected.
  - Committed 2026-11-15: `7d55d15` (six sources + Qdrant Cloud), `459ce8c` (abstention
    scoring, generator pinning), plus the eval runs and this file. Not pushed.
  - `docs/wiki/` still describes the single-site loader; needs a `/document` pass.

## State 2026-11-16 (branch `graph-design`, all uncommitted; commits were not requested)

- Alp's calls today: he hand-writes none of the graph pieces ("build it all"); G9 freeze
  and rebuild; he created the AuraDB Free instance himself (`NEO4J_*` in `.env`).
- Frozen snapshot `langchain-2026-11-16` (192 pages, id `3533e57389f9`). The eval
  collection of that name was ingested from it into the local store (4,797 vectors) and
  the harness is pinned to it (`EVAL_SNAPSHOT`). Structural graph built from it in
  AuraDB: 9,986 nodes, 19,143 relationships. Details and decisions G16-G19: `graph.md`.
- 98 tests pass, ruff clean. New deps: `neo4j`, `certifi`.
- **Every vector-arm score is now stale**: `evals/runs/*` and `compare.md` are from the
  July crawl. Not re-scored yet. Run in a plain terminal, not from Claude Code (long
  background jobs get killed here, `gotchas.md`); arms run one after another because
  embedded Qdrant allows one process:
  `foreach ($v in 'baseline','rerank-cohere','hybrid','hybrid-rerank') { uv run python -m sage.evals.harness run $v }; uv run python -m sage.evals.harness compare`
  Each `run` discards the July answers, regenerates 36 and scores them; it resumes if
  the free quota (resets 00:00 UTC) runs out. Stop condition: `compare.md` shows the
  four rows with snapshot `langchain-2026-11-16`.
- `structural`, `contextual` and `chunk-fixed` now point at `langchain-2026-11-16-*`
  collections that do not exist yet: `harness ingest <variant>` before running them.
- Needs Alp: relabel e011 (its page moved, `gotchas.md`); G15 labeling as before.
- 2026-11-18: `graph-local` strategy built (`adapters/graph_local.py`, ranking decision
  G20 in `graph.md`) with eval variant `graph-local`; 108 tests pass, ruff clean; one
  real answer verified against AuraDB. Not scored yet: add it to the plain-terminal
  eval loop above (`... 'hybrid-rerank','graph-local' ...`); AuraDB must be running.
- 2026-11-18: `text2cypher` strategy built (`adapters/text2cypher.py`; guard G12, context
  G21, correction G22, model G23 in `graph.md`) with eval variant `text2cypher`; 148
  tests pass, ruff clean; live queries and one full answer verified against AuraDB.
  Not scored yet: the eval loop becomes
  `... 'hybrid-rerank','graph-local','text2cypher' ...`. On the current golden set it
  is expected to lose (it answers passage questions with keyword `CONTAINS`); its claim
  needs G15's aggregate questions. "Source page retrieved" reads none for it (G21).
- Next build step: `graph-entity` (G10: LLM extraction into its own namespace, G11, G13).
- 2026-11-18: graph work committed (`e604113`), README rewritten for newcomers, graph
  knobs added to `.env.example`; branch `graph-design` pushed, PR #3 open to master; repo made public (Alp, 2026-11-18).

## Blocked

- `rerank-bge` stays segfault-blocked (`gotchas.md`).

## Next up

1. `hybrid-rerank` (the served stack) scored 2026-11-15, answerable n=22: faithfulness 0.891, relevancy 0.708, precision 0.842, recall 0.800, source page 0.818. Mixed vs `rerank-cohere` (0.961 / 0.723 / 0.896 / 0.759 / 0.773): best recall and source-page hit, but lower precision and faithfulness. This trips the revisit-if in `decisions.md`; keep/drop BM25 in the served stack is Alp's call. Graph design explainer for Alp: https://claude.ai/artifact/XJr9DH9Ktz8xjNZWj3yTBo (private; built from `graph.md`).
2. Score the contextual arms against the same generator and judge.
3. Alp labels ~20 more multi-hop questions: with 4 of 36, a GraphRAG win cannot show up
   in the scorecard. (Labeling is never delegated, see `decisions.md`.)
4. Native hybrid in Qdrant (sparse vectors with IDF + dense HNSW in one collection);
   the in-memory `rank_bm25` index rebuilds per process.
5. Neo4j graph from doc structure first (page links, heading tree, class mentions,
   zero LLM cost), LLM entity extraction as the paid comparison arm; each graph strategy
   stands alone (fusion with RRF optional). Design record: `graph.md` (decision nodes G1-G15).
   Built 2026-11-15 on branch `graph-design`: the `RetrievalStrategy` port, with today's
   flow as the `vector` strategy (`SAGE_STRATEGY`); 62 tests pass, real `sage.ask` verified.
   Built 2026-11-16 (same branch, uncommitted): frozen snapshot, `GraphStore` port +
   Neo4j adapter, structural builder; the graph is live in AuraDB (see below).
6. Machine limit: 3.6 GB RAM, Docker not running. Local Neo4j + Qdrant server will not
   fit; the free managed tiers (AuraDB Free, Qdrant Cloud free) are the realistic
   "free" option, and both pause when idle.
