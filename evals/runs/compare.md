# Variant comparison — latest run per variant

| variant | date | generator | answerable n | faithfulness | answer relevancy | llm context precision with reference | context recall | source page retrieved | declined when unanswerable |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 2026-11-10 | nvidia/nemotron-3.5-super-vl:free | 22 | 0.967 | 0.781 | 0.656 | 0.720 | 0.773 | 1.000 |
| rerank-cohere | 2026-11-15 | nvidia/nemotron-3.5-super-vl:free | 22 | 0.961 (-0.006) | 0.723 (-0.059) | 0.896 (+0.240) | 0.759 (+0.039) | 0.773 (+0.000) | 1.000 (+0.000) |
| hybrid | 2026-11-15 | nvidia/nemotron-3.5-super-vl:free | 22 | 0.951 (-0.016) | 0.734 (-0.047) | 0.797 (+0.141) | 0.735 (+0.015) | 0.727 (-0.045) | 1.000 (+0.000) |
| hybrid-rerank | 2026-11-15 | nvidia/nemotron-3.5-super-vl:free | 22 | 0.891 (-0.075) | 0.708 (-0.073) | 0.842 (+0.186) | 0.800 (+0.080) | 0.818 (+0.045) | 1.000 (+0.000) |

_The four RAGAS metrics are means over answerable questions only; unanswerable ones are scored by whether the answer declined. Deltas in parentheses are vs baseline, positive = better. Compare rows only when generator and judge match._
