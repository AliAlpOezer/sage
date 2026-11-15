# Scorecard — hybrid-rerank
_what the app serves: dense + BM25 -> RRF -> Cohere Rerank -> keep top_k_
Run: 2026-11-15  ·  scored 36/36 triples  ·  generator `nvidia/nemotron-3.5-super-vl:free`  ·  judge `nvidia/nemotron-3.5-super-vl:free`

Config: chunker=`recursive` top_k=5 assembly=`edges` reranker=`cohere` retrieve_k=30 collection=`langchain-docs`

## Answerable questions (n=22)

| metric | stage | mean | unscored |
|---|---|---|---|
| faithfulness | generation | 0.891 | 0 |
| answer_relevancy | generation | 0.708 | 0 |
| llm_context_precision_with_reference | retrieval | 0.842 | 0 |
| context_recall | retrieval | 0.800 | 0 |

**Weakest: `answer_relevancy` (0.708, generation).**

Labeled source page retrieved (no judge involved): 18/22 (0.818); missed: e003, e027, h002, m017.

## Unanswerable questions (n=14)

Correctly declined: 14/14 (1.000); unscored: 0.
