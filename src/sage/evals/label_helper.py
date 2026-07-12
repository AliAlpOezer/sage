"""Build a hand-labeling worksheet: each candidate + the real source-doc excerpts.

Scaffolding for Day-30 labeling. It pulls the ingested chunk text for each
candidate's source_urls straight from Qdrant (read-only, no API calls) so you can
write ground_truth while reading the exact passage. It deliberately does NOT write
ground_truth — labeling is never delegated (sprint protocol).

Run:  uv run python -m sage.evals.label_helper
Out:  evals/ragset_v1.worksheet.md
"""

import json
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient

from sage.config import Settings

CANDIDATES = Path("evals/candidates_v1.jsonl")
OUT = Path("evals/ragset_v1.worksheet.md")
PER_PAGE_CHAR_CAP = 900  # keep the worksheet readable


def _load_corpus_by_url(settings: Settings) -> dict[str, str]:
    """url -> concatenated chunk text (ordered by position)."""
    client = QdrantClient(path=settings.qdrant_path)
    chunks: dict[str, list[tuple[int, str]]] = defaultdict(list)
    offset = None
    while True:
        pts, offset = client.scroll(
            settings.collection, limit=512, with_payload=True, with_vectors=False, offset=offset
        )
        for p in pts:
            pl = p.payload or {}
            url = pl.get("source_url", "")
            chunks[url].append((pl.get("position", 0), pl.get("text", "")))
        if offset is None:
            break
    client.close()
    return {u: "\n".join(t for _, t in sorted(cs)) for u, cs in chunks.items()}


def main() -> None:
    settings = Settings.from_env()
    corpus = _load_corpus_by_url(settings)
    cands = [
        json.loads(line)
        for line in CANDIDATES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    out: list[str] = []
    out.append("# Hand-labeling worksheet — ragset v1")
    out.append("")
    out.append("For each question you want to keep: read the excerpt(s), then **write the")
    out.append("answer in your own words** on its `A[id]:` line. Leave the line blank to")
    out.append("DROP that question (blank = not kept — this blank/filled choice IS your")
    out.append("curation down to 30-50). Excerpts are the ingested chunks for each")
    out.append("source_url; they are reading aids, not answers. For `unanswerable`")
    out.append("questions the correct ground_truth is a refusal, e.g. `Not covered in the corpus.`")
    out.append("")
    out.append("When done:  `uv run python -m sage.evals.build_ragset`  → writes ragset_v1.jsonl")
    out.append("")
    by_cat: dict[str, int] = defaultdict(int)
    for c in cands:
        by_cat[c["category"]] += 1
    out.append("Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    out.append("")

    for c in cands:
        out.append(f"## {c['id']} · {c['category']}")
        out.append(f"**Q:** {c['question']}")
        if c.get("notes"):
            out.append(f"_notes: {c['notes']}_")
        if not c.get("source_urls"):
            out.append("> (unanswerable — expected behavior: decline / 'not in the corpus')")
        for url in c.get("source_urls", []):
            text = corpus.get(url, "")
            short = url.replace("https://docs.langchain.com/oss/python/", "")
            if not text:
                out.append(f"- **{short}** — ⚠️ no chunks found for this URL (fix source_urls?)")
                continue
            excerpt = text[:PER_PAGE_CHAR_CAP].replace("\n\n", "\n").strip()
            out.append(f"- **{short}**:")
            out.append("  > " + excerpt.replace("\n", "\n  > "))
        # The fill-in line: everything after the colon (this line only) is parsed
        # by build_ragset. Leave blank to drop the question.
        out.append(f"**A[{c['id']}]:** ")
        out.append("")

    OUT.write_text("\n".join(out), encoding="utf-8")
    missing = sum(
        1
        for c in cands
        for u in c.get("source_urls", [])
        if not corpus.get(u)
    )
    print(f"wrote {OUT} — {len(cands)} candidates, {missing} source_urls with no matching chunks")


if __name__ == "__main__":
    main()
