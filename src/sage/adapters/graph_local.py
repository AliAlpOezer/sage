"""RetrievalStrategy adapter: `graph-local`, one hop out from vector seeds in the structural graph.

1. Seed: the `graph_seed_k` chunks nearest the question in Neo4j's own vector index
   (graph.md G5). Qdrant is never touched (invariant 1).
2. Expand one hop from each seed: the chunks before and after it (NEXT), the rest of its
   section, the chunk most similar to the question on each page its page links to or is
   linked from (LINKS_TO), and the chunks that mention one of its symbols, a rare symbol
   counting for more (G19).
3. Support: a candidate's support is the sum, over the seeds that reach it, of the seed's
   similarity times the weight of its strongest edge to the candidate. A chunk several
   relevant seeds point at is the bridge a multi-hop question needs.
4. Rank: RRF of two orderings of the seeds plus the best-supported candidates, one by
   similarity to the question, one by support (G20). Ranks, not raw scores, so the two
   signals need no calibration against each other.
"""

import asyncio
from collections import defaultdict
from collections.abc import Iterable, Mapping

from sage.adapters.rrf import fuse
from sage.config import Settings
from sage.factory import make_embedder, make_graph_store, register_strategy
from sage.graph.current import check_build
from sage.graph.schema import (
    CHUNK,
    CHUNK_VECTOR_INDEX,
    EMBEDDING,
    HAS_CHUNK,
    LINKS_TO,
    MENTIONS,
    NEXT,
    PAGE,
    PAGE_HAS_SECTION,
    SECTION,
    SYMBOL,
)
from sage.models import Chunk, ScoredChunk

# Edge weights, relative to each other only (support is ranked, never added to similarity).
# A neighbouring chunk continues the seed's text; a section sibling shares its heading;
# a linked page is one the author chose to point at but is a whole page away. A shared
# symbol weighs 1/sqrt(chunks mentioning it): 0.71 for a symbol two chunks share, 0.1
# for a hub mentioned in a hundred.
WEIGHT_NEXT = 1.0
WEIGHT_SECTION = 0.7
WEIGHT_LINK = 0.4
# Best-supported non-seed candidates that join the seeds in the final ranking.
POOL = 50


def _labels(node_type) -> str:
    return f"`{node_type.label}`:`{node_type.namespace}`"


_C, _S, _P, _Y = _labels(CHUNK), _labels(SECTION), _labels(PAGE), _labels(SYMBOL)
# Page->Section and Section->Section share one relationship type.
_HAS_SECTION = PAGE_HAS_SECTION.type

SEED_QUERY = (
    f"CYPHER 25 MATCH (c:`{CHUNK.label}`) "
    f"SEARCH c IN (VECTOR INDEX `{CHUNK_VECTOR_INDEX}` FOR $vector LIMIT $n) SCORE AS similarity "
    f"RETURN c.`{CHUNK.key}` AS id, similarity"
)

EXPAND_QUERY = (
    "CYPHER 25 UNWIND $seeds AS seed "
    f"MATCH (s:{_C} {{`{CHUNK.key}`: seed}}) "
    "CALL (s) { "
    f"  MATCH (s)-[:`{NEXT.type}`]-(c:{_C}) "
    "   RETURN c, $w_next AS weight "
    "  UNION ALL "
    f"  MATCH (s)<-[:`{HAS_CHUNK.type}`]-(:{_S})-[:`{HAS_CHUNK.type}`]->(c:{_C}) WHERE c <> s "
    "   RETURN c, $w_section AS weight "
    "  UNION ALL "
    f"  MATCH (:{_P} {{`{PAGE.key}`: s.source_url}})-[:`{LINKS_TO.type}`]-(linked:{_P}) "
    "   CALL (linked) { "
    f"    MATCH (linked)-[:`{_HAS_SECTION}`]->+(:{_S})-[:`{HAS_CHUNK.type}`]->(c:{_C}) "
    f"    RETURN c ORDER BY vector.similarity.cosine(c.`{EMBEDDING}`, $vector) DESC LIMIT 1 "
    "   } "
    "   RETURN c, $w_link AS weight "
    "  UNION ALL "
    f"  MATCH (s)-[:`{MENTIONS.type}`]->(y:{_Y})<-[:`{MENTIONS.type}`]-(c:{_C}) WHERE c <> s "
    f"   RETURN c, 1.0 / sqrt(COUNT {{ (y)<-[:`{MENTIONS.type}`]-() }}) AS weight "
    "} "
    f"WITH seed, c, max(weight) AS weight "
    f"RETURN seed, c.`{CHUNK.key}` AS candidate, weight, "
    f"vector.similarity.cosine(c.`{EMBEDDING}`, $vector) AS similarity"
)

FETCH_QUERY = (
    "CYPHER 25 UNWIND $ids AS id "
    f"MATCH (c:{_C} {{`{CHUNK.key}`: id}}) "
    f"RETURN c.`{CHUNK.key}` AS id, c.text AS text, c.source_url AS source_url, c.title AS title, "
    "c.position AS position"
)


def support(
    seeds: Mapping[str, float], edges: Iterable[tuple[str, str, float]]
) -> dict[str, float]:
    """Sum over seeds of (seed similarity x weight) for each `(seed, candidate, weight)` edge.

    `edges` holds one row per (seed, candidate) pair, already reduced to its strongest
    edge, so a candidate gains once per seed that reaches it, not once per path.
    """
    total: dict[str, float] = defaultdict(float)
    for seed, candidate, weight in edges:
        if candidate != seed:
            total[candidate] += seeds[seed] * weight
    return dict(total)


@register_strategy("graph-local")
class GraphLocalStrategy:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedder = make_embedder(settings)
        self.store = make_graph_store(settings)

    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        check_build(self.store, self.settings, embeds_questions=True)
        vector = asyncio.run(self.embedder.embed([question]))[0]
        seed_rows = self.store.read(
            SEED_QUERY, {"vector": vector, "n": max(k, self.settings.graph_seed_k)}
        )
        seeds = {row["id"]: row["similarity"] for row in seed_rows}

        edges = self.store.read(
            EXPAND_QUERY,
            {
                "seeds": list(seeds),
                "vector": vector,
                "w_next": WEIGHT_NEXT,
                "w_section": WEIGHT_SECTION,
                "w_link": WEIGHT_LINK,
            },
        )
        supported = support(
            seeds, ((e["seed"], e["candidate"], e["weight"]) for e in edges)
        )
        similarity = {**{e["candidate"]: e["similarity"] for e in edges}, **seeds}

        def by(signal: Mapping[str, float]):
            return lambda c: (-signal.get(c, 0.0), -similarity[c], c)

        reached = sorted((c for c in supported if c not in seeds), key=by(supported))
        pool = [*seeds, *reached[:POOL]]
        by_similarity = sorted(pool, key=by(similarity))
        by_support = sorted(
            (c for c in pool if supported.get(c, 0.0) > 0), key=by(supported)
        )
        fused = fuse([by_similarity, by_support])[:k]

        rows = {
            row["id"]: row
            for row in self.store.read(FETCH_QUERY, {"ids": [c for c, _ in fused]})
        }
        return [
            ScoredChunk(
                chunk=Chunk(
                    id=chunk_id,
                    text=rows[chunk_id]["text"],
                    source_url=rows[chunk_id]["source_url"],
                    title=rows[chunk_id]["title"],
                    position=rows[chunk_id]["position"],
                ),
                score=score,
            )
            for chunk_id, score in fused
        ]
