# Scorecard — baseline
_recursive chunks, top_k=5, edges assembly (the reference)_
Run: 2026-11-10  ·  scored 36/36 triples  ·  generator `nvidia/nemotron-3.5-super-vl:free`  ·  judge `nvidia/nemotron-3.5-super-vl:free`

Config: chunker=`recursive` top_k=5 assembly=`edges` reranker=`none` collection=`langchain-docs`

## Answerable questions (n=22)

| metric | stage | mean | unscored |
|---|---|---|---|
| faithfulness | generation | 0.967 | 0 |
| answer_relevancy | generation | 0.781 | 0 |
| llm_context_precision_with_reference | retrieval | 0.656 | 0 |
| context_recall | retrieval | 0.720 | 0 |

**Weakest: `llm_context_precision_with_reference` (0.656, retrieval).**

Labeled source page retrieved (no judge involved): 17/22 (0.773); missed: e001, e002, e003, e005, h002.

## Unanswerable questions (n=14)

Correctly declined: 14/14 (1.000); unscored: 0.
