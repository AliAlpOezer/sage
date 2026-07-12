# Eval-set candidates — hand-labeling worksheet (Day 30)

**Protocol: labeling is never delegated.** These 90 candidate questions were AI-drafted
from the *real* ingested corpus (185 pages of docs.langchain.com/oss/python, sampled
directly from the Qdrant index). Ground truth is deliberately blank — **you write it.**

## What to do
1. Open `candidates_v1.jsonl`. For each question you keep:
   - Read the doc(s) in `source_urls` and **write `ground_truth` in your own words** —
     the answer the corpus *should* support. Keep it short and checkable.
   - Fix `source_urls` if the real answer lives on a different/additional page.
   - For `unanswerable`: ground_truth should state the corpus doesn't cover it (e.g.
     "Not in the corpus — the docs don't specify this."). A good RAG system must decline,
     not hallucinate. Verify the ones marked "verify" (u012/u014) really aren't documented.
2. **Curate down to 30–50** you'd genuinely want answered. Drop weak ones.
3. Save the kept, labeled lines as `evals/ragset_v1.jsonl` (same schema).
4. Commit: `day 30: 30-50 hand-labeled ragset triples v1 [hand]`.

## Coverage (drafted)
| category | count | what it tests |
|---|---|---|
| easy | 30 | single-page factual recall |
| hard | 28 | exact identifiers / params / nuance — the **predicted weak spot** (dense-only retrieval on `create_agent` params, error strings, `wrap_tool_call`, `state_schema`, etc.) |
| multi-hop | 18 | answer spans 2–3 pages (memory+tool, handoff+persistence, rag+memory…) |
| unanswerable | 14 | out-of-scope / false-premise — must decline, not confabulate |

## Notes
- The Day-25 failure log was never filled in, so there are no logged failures to fold in.
  The `hard` set targets the *predicted* failure mode instead (exact-identifier retrieval).
- Aim for a mix skewed toward hard + multi-hop — that's where the naive baseline should
  bleed, and where W6 must show improvement.
- Schema per line: `{id, question, ground_truth, source_urls[], category, notes}`.
