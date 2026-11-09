"""Day-32/33 eval harness: change one knob -> re-run RAGAS -> diff vs baseline.

A *variant* is a named set of Settings overrides. Each variant gets a stable run
id (its name), a resumable answer cache, and a per-run markdown scorecard; every
scored run appends one row to an append-only history (evals/runs/index.jsonl) so
W5 and W6 stay comparable. `compare` diffs the latest run of every variant against
the baseline — that delta is what makes a knob-change "measured, not vibed".

Variants that change chunking re-index the corpus, so they live in their own Qdrant
collection and must be ingested first (costs embedding $; gated behind `ingest`).
Query-time knobs (top_k, assembly order) reuse the baseline collection — cheap.

    uv run python -m sage.evals.harness list
    uv run python -m sage.evals.harness ingest chunk-fixed        # only chunker variants
    uv run python -m sage.evals.harness run assembly-naive        # generate + score
    uv run python -m sage.evals.harness run baseline --phase score
    uv run python -m sage.evals.harness compare                   # -> runs/compare.md
"""

import argparse
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd
from ragas import EvaluationDataset, SingleTurnSample, evaluate

from sage import ingest as ingest_mod
from sage.config import Settings
from sage.evals.dataset import load_triples
from sage.evals.judge import build_judge, default_metrics, default_run_config
from sage.evals.scorecard import METRIC_COLS, METRIC_STAGE, RAGSET
from sage.service import answer as pipeline_answer

RUNS_DIR = Path("evals/runs")
INDEX = RUNS_DIR / "index.jsonl"  # append-only longitudinal history

# name -> (Settings overrides, one-line description). "baseline" is the reference.
# assembly-naive is the Day-33 Lost-in-the-Middle control arm. chunk-* re-index,
# so they carry their own collection and must be ingested before `run`.
VARIANTS: dict[str, tuple[dict, str]] = {
    "baseline": ({}, "recursive chunks, top_k=5, edges assembly (the reference)"),
    "assembly-naive": ({"assembly_order": "naive"}, "pure score order (Day-33 reorder control)"),
    "topk-3": ({"top_k": 3}, "fewer chunks: precision up, recall risk"),
    "topk-8": ({"top_k": 8}, "more chunks: recall up, precision/cost risk"),
    "rerank-bge": (
        {"reranker": "bge", "retrieve_k": 30},
        "Day-37 precision stage, local BGE -- BLOCKED on this machine, see gotchas.md",
    ),
    "rerank-cohere": (
        {"reranker": "cohere", "retrieve_k": 30},
        "Day-37 precision stage: retrieve 30 -> Cohere Rerank v2 -> keep top_k",
    ),
    "chunk-fixed": (
        {"chunker": "fixed", "collection": "langchain-docs-fixed"},
        "fixed-size chunks, structure-blind (needs ingest)",
    ),
    "hybrid": (
        {"sparse_retriever": "bm25", "retrieve_k": 30},
        "Day-36: dense + BM25 -> RRF fusion (targets context_recall)",
    ),
    "structural": (
        {"chunker": "structural", "collection": "langchain-docs-structural"},
        "Day-38 free control: heading-breadcrumb prefix, no LLM (needs ingest)",
    ),
    "contextual": (
        {"chunker": "contextual", "collection": "langchain-docs-contextual"},
        "Day-38: LLM page blurb + breadcrumb prefix before embedding (needs ingest)",
    ),
    # "chunk-semantic": stretch goal — needs a hand-written semantic chunker
    # (embedding-based boundary detection). Own it yourself, then register
    # "semantic" in adapters/chunkers.py and add the variant here.
}


def variant_settings(name: str) -> Settings:
    if name not in VARIANTS:
        raise SystemExit(f"unknown variant {name!r}; try: {', '.join(VARIANTS)}")
    overrides, _ = VARIANTS[name]
    return replace(Settings.from_env(), **overrides)


def _run_dir(name: str) -> Path:
    d = RUNS_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- generate: run the pipeline variant per triple, cache answers (resumable) ---
def phase_generate(name: str, settings: Settings) -> None:
    triples = load_triples(RAGSET)
    answers_path = _run_dir(name) / "answers.jsonl"
    done = set()
    if answers_path.exists():
        for line in answers_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    todo = [t for t in triples if t.id not in done]
    print(f"[{name}] generate: {len(triples)} triples, {len(done)} cached, {len(todo)} to run")
    with answers_path.open("a", encoding="utf-8") as f:
        for i, t in enumerate(todo, 1):
            try:
                ans = pipeline_answer(t.question, settings=settings)
                rec = {
                    "id": t.id,
                    "question": t.question,
                    "answer": ans.answer,
                    "retrieved_contexts": [s.text for s in ans.sources],
                    "retrieved_urls": [s.url for s in ans.sources],
                }
            except Exception as e:  # noqa: BLE001 — log & continue; resume later
                print(f"  [{i}/{len(todo)}] {t.id} FAILED: {type(e).__name__}: {str(e)[:120]}")
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  [{i}/{len(todo)}] {t.id} ok ({len(rec['retrieved_contexts'])} ctx)")


# --- score: RAGAS over the cached answers -> per-run scorecard + history row ---
def phase_score(name: str, settings: Settings) -> None:
    triples = {t.id: t for t in load_triples(RAGSET)}
    answers_path = _run_dir(name) / "answers.jsonl"
    if not answers_path.exists():
        raise FileNotFoundError(f"{answers_path} missing — run `run {name} --phase generate` first.")
    answers = {}
    for line in answers_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            answers[rec["id"]] = rec

    ids = [i for i in triples if i in answers]
    if not ids:
        raise SystemExit(
            f"[{name}] score: 0/{len(triples)} triples have cached answers — "
            f"the generate phase produced nothing scoreable (check its FAILED lines above)."
        )
    def sample(i: str) -> SingleTurnSample:
        return SingleTurnSample(
            user_input=triples[i].question,
            response=answers[i]["answer"],
            retrieved_contexts=answers[i]["retrieved_contexts"],
            reference=triples[i].ground_truth,
        )

    judge = settings.resolved_judge_model
    scores_path = _run_dir(name) / "scores.jsonl"
    scored = _load_scores(scores_path, judge)
    todo = [i for i in ids if not _score_complete(scored.get(i))]
    print(
        f"[{name}] score: {len(ids)} samples, {len(ids) - len(todo)} already scored "
        f"by judge={judge}, {len(todo)} to score"
    )

    llm, emb = build_judge(settings)
    dead_batches = 0
    with scores_path.open("a", encoding="utf-8") as f:
        for start in range(0, len(todo), SCORE_BATCH):
            batch = todo[start : start + SCORE_BATCH]
            result = evaluate(
                dataset=EvaluationDataset(samples=[sample(i) for i in batch]),
                metrics=default_metrics(),
                llm=llm,
                embeddings=emb,
                run_config=default_run_config(settings),
                show_progress=False,
            )
            rows = result.to_pandas().to_dict("records")
            if not any(_num(r.get(c)) is not None for r in rows for c in METRIC_COLS):
                # Every metric failed: the judge is down or out of quota, not this
                # batch's fault. Don't spend its attempts; stop after two in a row.
                dead_batches += 1
                print(f"  {batch}: every metric failed (judge unreachable or out of quota?)")
                if dead_batches == 2:
                    break
                continue
            dead_batches = 0
            for i, r in zip(batch, rows, strict=True):
                scored[i] = _merge_score(scored.get(i), i, judge, r)
                f.write(json.dumps(scored[i]) + "\n")
                f.flush()
            done = sum(_score_complete(scored.get(i)) for i in ids)
            print(f"  scored {', '.join(batch)}  ({done}/{len(ids)} complete)")

    incomplete = [i for i in ids if not _score_complete(scored.get(i))]
    if incomplete:
        print(f"[{name}] {len(incomplete)} samples incomplete; re-run the score phase to resume.")
        return
    df = pd.DataFrame([{c: scored[i][c] for c in METRIC_COLS} for i in ids])
    df.insert(0, "id", ids)
    df["category"] = [triples[i].category for i in ids]
    df["user_input"] = [triples[i].question for i in ids]
    df["response"] = [answers[i]["answer"] for i in ids]
    _write_run(name, df, settings, n_total=len(triples))


# Score this many samples per RAGAS call, so a quota stop loses one batch, not the run.
SCORE_BATCH = 4
# A sample whose metrics stay NaN after this many judge attempts is accepted as NaN
# (the scorecard reports NaN counts) instead of blocking the scorecard forever.
MAX_SCORE_ATTEMPTS = 3


def _num(value: object) -> float | None:
    """A metric value as float, or None when it is missing or NaN."""
    if value is None or pd.isna(value):
        return None
    return float(value)


def _load_scores(path: Path, judge: str) -> dict[str, dict]:
    """Latest saved row per sample id, from this judge only (another judge's scores
    are not comparable, so switching judge re-scores everything)."""
    rows: dict[str, dict] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and (row := json.loads(line))["judge"] == judge:
                rows[row["id"]] = row
    return rows


def _score_complete(row: dict | None) -> bool:
    if row is None:
        return False
    has_all = all(row.get(c) is not None for c in METRIC_COLS)
    return has_all or row["attempts"] >= MAX_SCORE_ATTEMPTS


def _merge_score(old: dict | None, sample_id: str, judge: str, result: dict) -> dict:
    """New attempt's values, keeping any metric an earlier attempt already got."""
    old = old or {}
    merged = {c: old.get(c) if old.get(c) is not None else _num(result.get(c)) for c in METRIC_COLS}
    return {"id": sample_id, "judge": judge, "attempts": old.get("attempts", 0) + 1, **merged}


def _means(df: pd.DataFrame) -> dict[str, float]:
    present = [c for c in METRIC_COLS if c in df.columns]
    return {c: float(df[c].mean()) for c in present}


def _write_run(name: str, df: pd.DataFrame, settings: Settings, n_total: int) -> None:
    run_dir = _run_dir(name)
    df.to_csv(run_dir / "details.csv", index=False)
    means = _means(df)
    present = list(means)
    weakest = min(means, key=lambda c: means[c]) if means else None

    _, desc = VARIANTS[name]
    lines = [
        f"# Scorecard — {name}",
        f"_{desc}_",
        f"Run: {datetime.now().astimezone().date().isoformat()}  ·  scored {len(df)}/{n_total} triples  ·  judge `{settings.resolved_judge_model}`",
        "",
        (
            f"Config: chunker=`{settings.chunker}` top_k={settings.top_k} "
            f"assembly=`{settings.assembly_order}` reranker=`{settings.reranker}`"
            f"{f' retrieve_k={settings.retrieve_k}' if settings.reranker != 'none' else ''} "
            f"collection=`{settings.collection}`"
        ),
        "",
        "| metric | stage | mean |",
        "|---|---|---|",
    ]
    for c in present:
        lines.append(f"| {c} | {METRIC_STAGE[c]} | {means[c]:.3f} |")
    if weakest:
        lines.append("")
        lines.append(f"**Weakest: `{weakest}` ({means[weakest]:.3f}, {METRIC_STAGE[weakest]}).**")
    (run_dir / "scorecard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "run": name,
        "date": datetime.now().astimezone().date().isoformat(),
        "n": len(df),
        "means": {c: round(means[c], 4) for c in present},
        "config": {
            "chunker": settings.chunker,
            "top_k": settings.top_k,
            "assembly_order": settings.assembly_order,
            "reranker": settings.reranker,
            "retrieve_k": settings.retrieve_k,
            "collection": settings.collection,
        },
    }
    with INDEX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[{name}] wrote {run_dir/'scorecard.md'} + details.csv; appended to {INDEX}")


# --- compare: latest run of every variant, delta vs baseline -----------------
def cmd_compare() -> None:
    if not INDEX.exists():
        raise SystemExit(f"{INDEX} not found — score at least one run first.")
    latest: dict[str, dict] = {}
    for line in INDEX.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            latest[row["run"]] = row  # last wins = most recent
    if "baseline" not in latest:
        print("(no baseline scored yet — deltas omitted)")
    base = latest.get("baseline", {}).get("means", {})

    metrics = [c for c in METRIC_COLS if any(c in r["means"] for r in latest.values())]
    header = "| variant | date | n | " + " | ".join(m.replace("_", " ") for m in metrics) + " |"
    sep = "|---|---|---|" + "---|" * len(metrics)
    out = ["# Variant comparison — latest run per variant", "", header, sep]
    for name in VARIANTS:  # stable order
        if name not in latest:
            continue
        r = latest[name]
        cells = []
        for m in metrics:
            v = r["means"].get(m)
            if v is None:
                cells.append("—")
            elif name != "baseline" and m in base:
                cells.append(f"{v:.3f} ({v - base[m]:+.3f})")
            else:
                cells.append(f"{v:.3f}")
        out.append(f"| {name} | {r['date']} | {r['n']} | " + " | ".join(cells) + " |")
    out += ["", "_Deltas in parentheses are vs baseline. Positive = better (all four metrics are higher-is-better)._"]
    text = "\n".join(out) + "\n"
    (RUNS_DIR / "compare.md").write_text(text, encoding="utf-8")
    print(text)


def cmd_ingest(name: str) -> None:
    import asyncio

    settings = variant_settings(name)
    if not (VARIANTS[name][0].get("collection")):
        raise SystemExit(f"{name} reuses the baseline collection — no separate ingest needed.")
    print(f"[{name}] ingesting into collection={settings.collection} chunker={settings.chunker} ...")
    asyncio.run(ingest_mod.run(settings))


def cmd_list() -> None:
    print("variants:")
    for name, (ov, desc) in VARIANTS.items():
        tag = " [needs ingest]" if ov.get("collection") else ""
        print(f"  {name:16s} {desc}{tag}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("compare")
    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("variant")
    p_run = sub.add_parser("run")
    p_run.add_argument("variant")
    p_run.add_argument("--phase", choices=["generate", "score", "all"], default="all")
    args = ap.parse_args()

    if args.cmd == "list":
        cmd_list()
    elif args.cmd == "compare":
        cmd_compare()
    elif args.cmd == "ingest":
        cmd_ingest(args.variant)
    elif args.cmd == "run":
        settings = variant_settings(args.variant)
        if args.phase in ("generate", "all"):
            phase_generate(args.variant, settings)
        if args.phase in ("score", "all"):
            phase_score(args.variant, settings)


if __name__ == "__main__":
    main()
