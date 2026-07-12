"""Parse the hand-filled worksheet into evals/ragset_v1.jsonl (Day-30 output).

The worksheet (built by label_helper) has one `**A[id]:** ...` line per candidate.
You write the ground-truth answer after the colon in your own words; a blank line
means "drop this question" (that is your curation down to 30-50). This script reads
those answers, joins them back to the candidate metadata, and writes the versioned
eval set. It never invents an answer — blank stays dropped (labeling is not delegated).

Run:  uv run python -m sage.evals.build_ragset
Out:  evals/ragset_v1.jsonl   (only candidates with a non-blank A[id]: line)
"""

import json
import re
from pathlib import Path

CANDIDATES = Path("evals/candidates_v1.jsonl")
WORKSHEET = Path("evals/ragset_v1.worksheet.md")
OUT = Path("evals/ragset_v1.jsonl")

# `**A[e001]:** the answer text` — capture id and the rest of that one line.
ANSWER_RE = re.compile(r"^\*\*A\[(?P<id>[^\]]+)\]:\*\*\s*(?P<ans>.*)$")


def parse_answers(worksheet: Path) -> dict[str, str]:
    answers: dict[str, str] = {}
    for line in worksheet.read_text(encoding="utf-8").splitlines():
        m = ANSWER_RE.match(line.strip())
        if not m:
            continue
        ans = m.group("ans").strip()
        # strip a stray placeholder if the line was never touched
        if ans and ans not in {"_", "...", "TODO", "TBD"}:
            answers[m.group("id")] = ans
    return answers


def main() -> None:
    if not WORKSHEET.exists():
        raise FileNotFoundError(
            f"{WORKSHEET} not found — run: uv run python -m sage.evals.label_helper"
        )
    candidates = {
        json.loads(line)["id"]: json.loads(line)
        for line in CANDIDATES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    answers = parse_answers(WORKSHEET)

    unknown = sorted(set(answers) - set(candidates))
    if unknown:
        raise ValueError(f"worksheet has answers for unknown ids: {unknown}")

    kept = [cid for cid in candidates if cid in answers]  # preserve candidate order
    with OUT.open("w", encoding="utf-8") as f:
        for cid in kept:
            c = candidates[cid]
            rec = {
                "id": cid,
                "question": c["question"],
                "ground_truth": answers[cid],
                "source_urls": c.get("source_urls", []),
                "category": c.get("category", "easy"),
                "notes": c.get("notes", ""),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    by_cat: dict[str, int] = {}
    for cid in kept:
        cat = candidates[cid].get("category", "easy")
        by_cat[cat] = by_cat.get(cat, 0) + 1
    dropped = len(candidates) - len(kept)
    print(f"wrote {OUT}: {len(kept)} labeled triples ({dropped} dropped)")
    print("by category: " + ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    if len(kept) < 30:
        print(f"WARNING: only {len(kept)} labeled - target is 30-50. Fill more A[id]: lines.")


if __name__ == "__main__":
    main()
