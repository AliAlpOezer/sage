# Day 25 — 10-question failure log

Ask real questions you'd genuinely want answered. For each: judge the ANSWER
(right/wrong/partial) and the GROUNDING (did the retrieved sources actually
contain the answer?). The failure column feeds W5 — be specific.

Failure taxonomy (from docs/wiki/concepts/rag-pipeline.md):
- `retrieval-miss` — right page exists in corpus, didn't reach top-k
- `rank` — right chunk retrieved but buried; wrong chunk dominated
- `chunking` — answer split across chunks / heading orphaned / context lost
- `generation` — good context, bad answer (hallucination, missed the point)
- `corpus-gap` — the docs genuinely don't contain it
- `ok` — no failure

| # | Question | Answer quality | Grounding | Failure type | Notes |
|---|----------|----------------|-----------|--------------|-------|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |
| 3 |  |  |  |  |  |
| 4 |  |  |  |  |  |
| 5 |  |  |  |  |  |
| 6 |  |  |  |  |  |
| 7 |  |  |  |  |  |
| 8 |  |  |  |  |  |
| 9 |  |  |  |  |  |
| 10 |  |  |  |  |  |

Tip: include at least two exact-identifier questions (`create_agent` params,
a specific error message) — that's where dense-only retrieval is predicted to
crack (docs/wiki/decisions/embedding-strategy.md).
