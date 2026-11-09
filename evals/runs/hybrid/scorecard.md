# Scorecard — hybrid
_Day-36: dense + BM25 -> RRF fusion (targets context_recall)_
Run: 2026-08-04  ·  scored 36/36 triples  ·  judge `auto/best-free`

Config: chunker=`recursive` top_k=5 assembly=`edges` reranker=`none` collection=`langchain-docs`

| metric | stage | mean |
|---|---|---|
| faithfulness | generation | 0.880 |
| answer_relevancy | generation | 0.650 |
| llm_context_precision_with_reference | retrieval | 0.564 |
| context_recall | retrieval | 0.629 |

**Weakest: `llm_context_precision_with_reference` (0.564, retrieval).**
