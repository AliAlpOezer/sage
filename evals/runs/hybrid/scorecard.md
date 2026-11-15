# Scorecard — hybrid
_Day-36: dense + BM25 -> RRF fusion (targets context_recall)_
Run: 2026-11-15  ·  scored 36/36 triples  ·  generator `nvidia/nemotron-3.5-super-vl:free`  ·  judge `nvidia/nemotron-3.5-super-vl:free`

Config: chunker=`recursive` top_k=5 assembly=`edges` reranker=`none` collection=`langchain-docs`

## Answerable questions (n=22)

| metric | stage | mean | unscored |
|---|---|---|---|
| faithfulness | generation | 0.951 | 0 |
| answer_relevancy | generation | 0.734 | 0 |
| llm_context_precision_with_reference | retrieval | 0.797 | 0 |
| context_recall | retrieval | 0.735 | 0 |

**Weakest: `answer_relevancy` (0.734, generation).**

Labeled source page retrieved (no judge involved): 16/22 (0.727); missed: e001, e002, e005, e014, h002, m017.

## Unanswerable questions (n=14)

Correctly declined: 14/14 (1.000); unscored: 0.
