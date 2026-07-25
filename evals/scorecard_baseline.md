# Baseline Scorecard — naive RAG
Run: 2026-07-25  ·  triples scored: 36/36

## Config
- judge: `llama-3.3-70b-versatile`
- generation: `nvidia/nemotron-3-super-120b-a12b:free`  ·  embedding: `openai/text-embedding-3-small`
- retrieval: top_k=5, store=qdrant, chunker=recursive

## Per-metric mean (higher = better; 0–1)
| metric | stage | mean | NaN |
|---|---|---|---|
| faithfulness | generation | 0.948 | 25 |
| answer_relevancy | generation | 0.620 | 16 |
| llm_context_precision_with_reference | retrieval | 0.593 | 19 |
| context_recall | retrieval | 0.679 | 23 |

**Weakest metric: `llm_context_precision_with_reference` (0.593, retrieval stage).** ← W6 target

## Worst 5 cases
### u004 · unanswerable · row-mean 0.000
- Q: What HNSW ef_construction value does Qdrant use by default?
- scores: faithfulness=NaN  answer_relevancy=0.00  llm_context_precision_with_reference=NaN  context_recall=NaN
- answer: The provided excerpts do not contain any information about Qdrant’s HNSW ef_construction default value. Therefore, the answer cannot be determined from the given documentation. The missing information is the default ef_construction setting used by Qdrant for HNSW indexing.

### h002 · hard · row-mean 0.000
- Q: What is the difference between passing checkpointer=True and checkpointer=InMemorySaver() to create_agent?
- scores: faithfulness=NaN  answer_relevancy=0.00  llm_context_precision_with_reference=0.00  context_recall=0.00
- answer: The provided excerpts do not show or explain what passing `checkpointer=True` does to `create_agent`. They only illustrate passing an actual checkpointer object (e.g., `MemorySaver()` or `InMemorySaver()`) as the `checkpointer` argument. Because no documentation excerpt describes the behavior or mea

### u002 · unanswerable · row-mean 0.000
- Q: How do I use create_agent in the JavaScript/TypeScript SDK?
- scores: faithfulness=NaN  answer_relevancy=0.00  llm_context_precision_with_reference=0.00  context_recall=NaN
- answer: The provided documentation excerpts do not contain any examples or instructions for using `create_agent` in the JavaScript/TypeScript SDK. All code samples demonstrating `create_agent` (in excerpts [1], [2], and [3]) are exclusively in Python. Excerpt [4] shows JavaScript/TypeScript code for connect

### u008 · unanswerable · row-mean 0.000
- Q: How do I fine-tune an LLM using LangChain?
- scores: faithfulness=NaN  answer_relevancy=0.00  llm_context_precision_with_reference=NaN  context_recall=NaN
- answer: The provided documentation excerpts do not contain any information on how to fine‑tune an LLM using LangChain. None of the sections [1]–[5] discuss fine‑tuning procedures or related guidance. To answer the question, you would need a section (e.g., “Fine‑tuning LLMs” or similar) that is missing from 

### u005 · unanswerable · row-mean 0.250
- Q: What is Anthropic's rate limit for the claude-sonnet-4-6 API?
- scores: faithfulness=1.00  answer_relevancy=0.00  llm_context_precision_with_reference=0.00  context_recall=0.00
- answer: The provided documentation excerpts do not specify Anthropic’s rate limit for the claude-sonnet-4-6 API. No rate‑limit numbers are given in the excerpts.

---
_Longitudinal record: append each week's run below this line so W6 can be compared to W5._
