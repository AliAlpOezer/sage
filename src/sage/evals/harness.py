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
import hashlib
import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pandas as pd
from ragas import EvaluationDataset, SingleTurnSample, evaluate

from sage import ingest as ingest_mod
from sage.config import Settings
from sage.evals.abstention import judge_abstention
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
    "hybrid-rerank": (
        {"sparse_retriever": "bm25", "reranker": "cohere", "retrieve_k": 30},
        "what the app serves: dense + BM25 -> RRF -> Cohere Rerank -> keep top_k",
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


# The golden set was labeled against the LangChain docs alone, so every variant is
# pinned to that corpus in the local store whatever `.env` serves; chunk-* variants
# override the collection. Retrieval stages are pinned off too, so the app serving
# hybrid + rerank never leaks into the baseline arm; variants switch them on.
EVAL_CORPUS = {
    "strategy": "vector",
    "sources": ("langchain",),
    "collection": "langchain-docs",
    "qdrant_url": "",
    "sparse_retriever": "none",
    "reranker": "none",
}


def variant_settings(name: str) -> Settings:
    if name not in VARIANTS:
        raise SystemExit(f"unknown variant {name!r}; try: {', '.join(VARIANTS)}")
    overrides, _ = VARIANTS[name]
    return replace(Settings.from_env(), **{**EVAL_CORPUS, **overrides})


def _run_dir(name: str) -> Path:
    d = RUNS_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- generate: run the pipeline variant per triple, cache answers (resumable) ---
def phase_generate(name: str, settings: Settings) -> None:
    triples = load_triples(RAGSET)
    answers_path = _run_dir(name) / "answers.jsonl"
    model = settings.resolved_generation_model
    cached = _read_jsonl(answers_path)
    # Answers from another generator are not comparable across variants: drop them
    # (git keeps the old file) so every arm of a comparison shares one generator.
    kept = [rec for rec in cached if rec.get("generator") == model]
    if len(kept) != len(cached):
        print(f"[{name}] discarding {len(cached) - len(kept)} answers not generated by {model}")
        answers_path.write_text(
            "".join(json.dumps(rec, ensure_ascii=False) + "\n" for rec in kept), encoding="utf-8"
        )
    done = {rec["id"] for rec in kept}
    todo = [t for t in triples if t.id not in done]
    print(
        f"[{name}] generate with {model}: {len(triples)} triples, "
        f"{len(done)} cached, {len(todo)} to run"
    )
    with answers_path.open("a", encoding="utf-8") as f:
        for i, t in enumerate(todo, 1):
            try:
                ans = pipeline_answer(t.question, settings=settings)
                rec = {
                    "id": t.id,
                    "question": t.question,
                    "answer": ans.answer,
                    "generator": model,
                    "strategy": ans.strategy,
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
    answers = {rec["id"]: rec for rec in _read_jsonl(answers_path)}

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

    def cols(i: str) -> Sequence[str]:
        return (ABSTAINED,) if triples[i].category == UNANSWERABLE else METRIC_COLS

    def complete(i: str) -> bool:
        return _score_complete(scored.get(i), cols(i))

    judge = settings.resolved_judge_model
    hashes = {i: _answer_hash(answers[i]) for i in ids}
    scores_path = _run_dir(name) / "scores.jsonl"
    scored = _load_scores(scores_path, judge, hashes)
    todo = [i for i in ids if not complete(i)]
    declines = [i for i in todo if triples[i].category == UNANSWERABLE]
    ragas = [i for i in todo if triples[i].category != UNANSWERABLE]
    print(
        f"[{name}] score: {len(ids)} samples, {len(ids) - len(todo)} already scored by "
        f"judge={judge}; to score: {len(ragas)} with RAGAS, {len(declines)} for abstention"
    )

    llm, emb = build_judge(settings)
    with scores_path.open("a", encoding="utf-8") as f:

        def save(i: str, result: dict) -> None:
            scored[i] = _merge_score(scored.get(i), i, judge, result, cols(i), hashes[i])
            f.write(json.dumps(scored[i]) + "\n")
            f.flush()

        dead = 0
        for i in declines:
            verdict = judge_abstention(llm.langchain_llm, triples[i].question, answers[i]["answer"])
            # No verdict twice in a row: the judge is down or out of quota, so stop
            # without spending these samples' attempts.
            dead = dead + 1 if verdict is None else 0
            if dead == 2:
                print("  abstention: judge unreachable or out of quota, stopping")
                break
            if verdict is not None:
                save(i, {ABSTAINED: verdict})
                print(f"  {i}: {'declined' if verdict else 'ANSWERED'}")

        dead = 0
        for start in range(0, len(ragas), SCORE_BATCH):
            batch = ragas[start : start + SCORE_BATCH]
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
                dead += 1
                print(f"  {batch}: every metric failed (judge unreachable or out of quota?)")
                if dead == 2:
                    break
                continue
            dead = 0
            for i, r in zip(batch, rows, strict=True):
                save(i, r)
            print(f"  scored {', '.join(batch)}  ({sum(complete(i) for i in ids)}/{len(ids)} complete)")

    incomplete = [i for i in ids if not complete(i)]
    if incomplete:
        print(f"[{name}] {len(incomplete)} samples incomplete; re-run the score phase to resume.")
        return
    df = pd.DataFrame([{c: scored[i].get(c) for c in (*METRIC_COLS, ABSTAINED)} for i in ids])
    df.insert(0, "id", ids)
    df["category"] = [triples[i].category for i in ids]
    df[SOURCE_HIT] = [_source_hit(triples[i].source_urls, answers[i]["retrieved_urls"]) for i in ids]
    df["user_input"] = [triples[i].question for i in ids]
    df["response"] = [answers[i]["answer"] for i in ids]
    generators = sorted({answers[i].get("generator", "unrecorded") for i in ids})
    _write_run(name, df, settings, n_total=len(triples), generator=" + ".join(generators))


UNANSWERABLE = "unanswerable"
# Score column for unanswerable triples: 1.0 = the answer declined, 0.0 = it answered.
ABSTAINED = "abstained"
# Judge-free retrieval check: did any hand-labeled source page reach the context?
SOURCE_HIT = "source_hit"


def _source_hit(gold_urls: Sequence[str], retrieved_urls: Sequence[str]) -> float | None:
    """1.0 if a labeled source page was retrieved, None when the triple names none."""
    return float(bool(set(gold_urls) & set(retrieved_urls))) if gold_urls else None
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


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _answer_hash(rec: dict) -> str:
    """Identifies what was scored, so a regenerated answer never reuses an old score."""
    blob = json.dumps([rec["answer"], rec["retrieved_contexts"]], ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _load_scores(path: Path, judge: str, hashes: dict[str, str] | None = None) -> dict[str, dict]:
    """Latest saved row per sample id, from this judge only (another judge's scores
    are not comparable, so switching judge re-scores everything) and, given `hashes`,
    only for the answer that is cached now."""
    rows: dict[str, dict] = {}
    for row in _read_jsonl(path):
        if row["judge"] != judge:
            continue
        if hashes is not None and row.get("answer_hash") != hashes.get(row["id"]):
            continue
        rows[row["id"]] = row
    return rows


def _score_complete(row: dict | None, cols: Sequence[str] = METRIC_COLS) -> bool:
    if row is None:
        return False
    has_all = all(row.get(c) is not None for c in cols)
    return has_all or row["attempts"] >= MAX_SCORE_ATTEMPTS


def _merge_score(
    old: dict | None,
    sample_id: str,
    judge: str,
    result: dict,
    cols: Sequence[str] = METRIC_COLS,
    answer_hash: str | None = None,
) -> dict:
    """New attempt's values, keeping any metric an earlier attempt already got."""
    old = old or {}
    merged = {c: old.get(c) if old.get(c) is not None else _num(result.get(c)) for c in cols}
    row = {"id": sample_id, "judge": judge, "attempts": old.get("attempts", 0) + 1, **merged}
    return row if answer_hash is None else {**row, "answer_hash": answer_hash}


def _means(df: pd.DataFrame) -> dict[str, float]:
    """The four RAGAS means, over answerable triples only."""
    answerable = df[df["category"] != UNANSWERABLE]
    means = {c: float(answerable[c].astype(float).mean()) for c in METRIC_COLS if c in df.columns}
    return {c: m for c, m in means.items() if not pd.isna(m)}


def _write_run(name: str, df: pd.DataFrame, settings: Settings, n_total: int, generator: str) -> None:
    run_dir = _run_dir(name)
    df.to_csv(run_dir / "details.csv", index=False)
    answerable = df[df["category"] != UNANSWERABLE]
    unanswerable = df[df["category"] == UNANSWERABLE]
    means = _means(df)
    present = list(means)
    weakest = min(means, key=lambda c: means[c]) if means else None
    declined = unanswerable[ABSTAINED].astype(float)
    abstention = None if declined.dropna().empty else float(declined.mean())

    _, desc = VARIANTS[name]
    lines = [
        f"# Scorecard — {name}",
        f"_{desc}_",
        (
            f"Run: {datetime.now().astimezone().date().isoformat()}  ·  scored {len(df)}/{n_total} triples  ·  "
            f"generator `{generator}`  ·  judge `{settings.resolved_judge_model}`"
        ),
        "",
        (
            f"Config: strategy=`{settings.strategy}` chunker=`{settings.chunker}` top_k={settings.top_k} "
            f"assembly=`{settings.assembly_order}` reranker=`{settings.reranker}`"
            f"{f' retrieve_k={settings.retrieve_k}' if settings.reranker != 'none' else ''} "
            f"collection=`{settings.collection}`"
        ),
        "",
        f"## Answerable questions (n={len(answerable)})",
        "",
        "| metric | stage | mean | unscored |",
        "|---|---|---|---|",
    ]
    for c in present:
        lines.append(f"| {c} | {METRIC_STAGE[c]} | {means[c]:.3f} | {int(answerable[c].isna().sum())} |")
    if weakest:
        lines.append("")
        lines.append(f"**Weakest: `{weakest}` ({means[weakest]:.3f}, {METRIC_STAGE[weakest]}).**")
    hits = answerable[SOURCE_HIT].astype(float).dropna()
    source_hit = None if hits.empty else float(hits.mean())
    if source_hit is not None:
        missed = answerable[answerable[SOURCE_HIT] == 0.0]["id"].tolist()
        tail = f"; missed: {', '.join(missed)}" if missed else ""
        lines.append("")
        lines.append(
            f"Labeled source page retrieved (no judge involved): {int(hits.sum())}/{len(hits)} "
            f"({source_hit:.3f}){tail}."
        )
    if len(unanswerable):
        lines += ["", f"## Unanswerable questions (n={len(unanswerable)})", ""]
        if abstention is None:
            lines.append("No abstention verdicts.")
        else:
            lines.append(
                f"Correctly declined: {int(declined.sum())}/{int(declined.notna().sum())} "
                f"({abstention:.3f}); unscored: {int(declined.isna().sum())}."
            )
        answered = unanswerable[declined == 0.0]["id"].tolist()
        if answered:
            lines.append(f"Answered anyway: {', '.join(answered)}.")
    (run_dir / "scorecard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    row = {
        "run": name,
        "date": datetime.now().astimezone().date().isoformat(),
        "n": len(df),
        "n_answerable": len(answerable),
        "means": {c: round(means[c], 4) for c in present},
        "abstention": None if abstention is None else round(abstention, 4),
        "source_hit": None if source_hit is None else round(source_hit, 4),
        "generator": generator,
        "judge": settings.resolved_judge_model,
        "config": {
            "strategy": settings.strategy,
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
    for row in _read_jsonl(INDEX):
        latest[row["run"]] = row  # last wins = most recent
    # Rows without n_answerable predate 2026-11-10, when the means still averaged in
    # the unanswerable triples; they cannot sit in one table with the newer ones.
    stale = sorted(n for n, r in latest.items() if "n_answerable" not in r)
    latest = {n: r for n, r in latest.items() if n not in stale}
    if "baseline" not in latest:
        print("(no baseline scored yet — deltas omitted)")
    base = latest.get("baseline", {})

    def cell(name: str, value: float | None, reference: float | None) -> str:
        if value is None:
            return "—"
        if name == "baseline" or reference is None:
            return f"{value:.3f}"
        return f"{value:.3f} ({value - reference:+.3f})"

    metrics = [c for c in METRIC_COLS if any(c in r["means"] for r in latest.values())]
    header = (
        "| variant | date | generator | answerable n | "
        + " | ".join(m.replace("_", " ") for m in metrics)
        + " | source page retrieved | declined when unanswerable |"
    )
    sep = "|---|---|---|---|" + "---|" * (len(metrics) + 2)
    out = ["# Variant comparison — latest run per variant", "", header, sep]
    for name in VARIANTS:  # stable order
        if name not in latest:
            continue
        r = latest[name]
        cells = [cell(name, r["means"].get(m), base.get("means", {}).get(m)) for m in metrics]
        cells.append(cell(name, r.get("source_hit"), base.get("source_hit")))
        cells.append(cell(name, r.get("abstention"), base.get("abstention")))
        out.append(
            f"| {name} | {r['date']} | {r['generator']} | {r['n_answerable']} | " + " | ".join(cells) + " |"
        )
    out += [
        "",
        (
            "_The four RAGAS metrics are means over answerable questions only; unanswerable "
            "ones are scored by whether the answer declined. Deltas in parentheses are vs "
            "baseline, positive = better. Compare rows only when generator and judge match._"
        ),
    ]
    if stale:
        out += ["", f"_Not shown (scored before the answerable/unanswerable split): {', '.join(stale)}._"]
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
