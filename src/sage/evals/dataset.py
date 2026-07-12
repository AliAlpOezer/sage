"""The eval set: hand-labeled (question, ground-truth, source) triples.

Schema — one JSON object per line in evals/ragset_v1.jsonl:
    id           str   stable id, e.g. "q001"
    question     str   the user question
    ground_truth str   HAND-WRITTEN reference answer (never AI-generated — protocol)
    source_urls  [str] doc URL(s) the answer comes from (human traceability + audit)
    category     str   one of: easy | hard | multi-hop | unanswerable
    notes        str   optional (e.g. "day-25 failure case", "exact-identifier")

ground_truth is the RAGAS `reference`; source_urls are for the human, not the metric.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = {"easy", "hard", "multi-hop", "unanswerable"}


@dataclass(frozen=True)
class Triple:
    id: str
    question: str
    ground_truth: str
    source_urls: list[str] = field(default_factory=list)
    category: str = "easy"
    notes: str = ""


def load_triples(path: str | Path) -> list[Triple]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — hand-label the eval set first (Day 30)."
        )
    triples: list[Triple] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        obj = json.loads(line)
        missing = {"id", "question", "ground_truth"} - obj.keys()
        if missing:
            raise ValueError(f"{path}:{lineno} missing fields {missing}")
        triples.append(
            Triple(
                id=str(obj["id"]),
                question=obj["question"],
                ground_truth=obj["ground_truth"],
                source_urls=list(obj.get("source_urls", [])),
                category=obj.get("category", "easy"),
                notes=obj.get("notes", ""),
            )
        )
    ids = [t.id for t in triples]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate triple ids")
    return triples
