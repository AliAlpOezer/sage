# Scorecard — rerank-cohere
_Day-37 precision stage: retrieve 30 -> Cohere Rerank v2 -> keep top_k_
Run: 2026-11-15  ·  scored 36/36 triples  ·  generator `nvidia/nemotron-3.5-super-vl:free`  ·  judge `nvidia/nemotron-3.5-super-vl:free`

Config: chunker=`recursive` top_k=5 assembly=`edges` reranker=`cohere` retrieve_k=30 collection=`langchain-docs`

## Answerable questions (n=22)

| metric | stage | mean | unscored |
|---|---|---|---|
| faithfulness | generation | 0.961 | 0 |
| answer_relevancy | generation | 0.723 | 0 |
| llm_context_precision_with_reference | retrieval | 0.896 | 0 |
| context_recall | retrieval | 0.759 | 0 |

**Weakest: `answer_relevancy` (0.723, generation).**

Labeled source page retrieved (no judge involved): 17/22 (0.773); missed: e002, e003, e005, h002, m017.

## Unanswerable questions (n=14)

Correctly declined: 14/14 (1.000); unscored: 0.
