"""Day-31 baseline scorecard: run RAGAS on the naive RAG baseline over the eval set.

Two phases, each resumable (free-tier rate limits make one-shot runs fragile):

  1. generate  — run the live baseline (service.answer) per triple, cache the
                 answer + retrieved contexts to evals/baseline_answers_v1.jsonl.
                 Re-runs skip triples already cached (resume after a rate-limit stall).
  2. score     — load cached answers, run the 4 RAGAS metrics, write:
                   evals/scorecard_baseline.md            (means + worst 5, longitudinal)
                   evals/scorecard_baseline_details.csv   (per-sample, for the 20% audit)

Run both:   uv run python -m sage.evals.scorecard
Just one:   uv run python -m sage.evals.scorecard --phase generate
            uv run python -m sage.evals.scorecard --phase score

All model calls are serial (max_workers=1) to stay under the free tier's 8 req/min.
Expect this to be slow over 30-50 triples — that is the rate limit, not a hang.
"""

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd
from ragas import EvaluationDataset, SingleTurnSample, evaluate

from sage.config import Settings
from sage.evals.dataset import load_triples
from sage.evals.judge import build_judge, default_metrics, default_run_config
from sage.service import answer as baseline_answer

EVALS_DIR = Path("evals")
RAGSET = EVALS_DIR / "ragset_v1.jsonl"
ANSWERS = EVALS_DIR / "baseline_answers_v1.jsonl"
SCORECARD = EVALS_DIR / "scorecard_baseline.md"
DETAILS = EVALS_DIR / "scorecard_baseline_details.csv"

METRIC_COLS = [
    "faithfulness",
    "answer_relevancy",
    "llm_context_precision_with_reference",
    "context_recall",
]
METRIC_STAGE = {
    "faithfulness": "generation",
    "answer_relevancy": "generation",
    "llm_context_precision_with_reference": "retrieval",
    "context_recall": "retrieval",
}


# --- phase 1: generate baseline answers (resumable cache) --------------------
def phase_generate(settings: Settings) -> None:
    triples = load_triples(RAGSET)
    done = set()
    if ANSWERS.exists():
        for line in ANSWERS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    todo = [t for t in triples if t.id not in done]
    print(f"generate: {len(triples)} triples, {len(done)} cached, {len(todo)} to run")
    with ANSWERS.open("a", encoding="utf-8") as f:
        for i, t in enumerate(todo, 1):
            try:
                ans = baseline_answer(t.question, settings=settings)
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


# --- phase 2: score with RAGAS + write scorecard -----------------------------
def phase_score(settings: Settings) -> None:
    triples = {t.id: t for t in load_triples(RAGSET)}
    if not ANSWERS.exists():
        raise FileNotFoundError(f"{ANSWERS} missing — run --phase generate first.")
    answers = {}
    for line in ANSWERS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            answers[rec["id"]] = rec

    ids = [i for i in triples if i in answers]
    samples = [
        SingleTurnSample(
            user_input=triples[i].question,
            response=answers[i]["answer"],
            retrieved_contexts=answers[i]["retrieved_contexts"],
            reference=triples[i].ground_truth,
        )
        for i in ids
    ]
    print(f"score: {len(samples)} samples with judge={settings.judge_model}")

    llm, emb = build_judge(settings)
    result = evaluate(
        dataset=EvaluationDataset(samples=samples),
        metrics=default_metrics(),
        llm=llm,
        embeddings=emb,
        run_config=default_run_config(settings),
    )
    df = result.to_pandas()
    df.insert(0, "id", ids)
    df["category"] = [triples[i].category for i in ids]
    df.to_csv(DETAILS, index=False)
    _write_scorecard(df, settings, n_total=len(triples))
    print(f"wrote {SCORECARD} and {DETAILS}")


def _write_scorecard(df: pd.DataFrame, settings: Settings, n_total: int) -> None:
    present = [c for c in METRIC_COLS if c in df.columns]
    means = {c: df[c].mean() for c in present}
    nan_counts = {c: int(df[c].isna().sum()) for c in present}
    weakest = min(means, key=lambda c: (means[c] if pd.notna(means[c]) else 1.0))

    # worst 5 by mean of available metric scores per row
    df = df.copy()
    df["_row_mean"] = df[present].mean(axis=1, skipna=True)
    worst = df.nsmallest(5, "_row_mean")

    lines: list[str] = []
    lines.append("# Baseline Scorecard — naive RAG")
    lines.append(f"Run: {date.today().isoformat()}  ·  triples scored: {len(df)}/{n_total}")
    lines.append("")
    lines.append("## Config")
    lines.append(f"- judge: `{settings.judge_model}`")
    lines.append(f"- generation: `{settings.generation_model}`  ·  embedding: `{settings.embedding_model}`")
    lines.append(f"- retrieval: top_k={settings.top_k}, store={settings.vector_store}, chunker={settings.chunker}")
    lines.append("")
    lines.append("## Per-metric mean (higher = better; 0–1)")
    lines.append("| metric | stage | mean | NaN |")
    lines.append("|---|---|---|---|")
    for c in present:
        m = means[c]
        lines.append(f"| {c} | {METRIC_STAGE[c]} | {('%.3f' % m) if pd.notna(m) else 'n/a'} | {nan_counts[c]} |")
    lines.append("")
    wm = means[weakest]
    lines.append(f"**Weakest metric: `{weakest}` ({('%.3f' % wm) if pd.notna(wm) else 'n/a'}, {METRIC_STAGE[weakest]} stage).** ← W6 target")
    lines.append("")
    lines.append("## Worst 5 cases")
    for _, r in worst.iterrows():
        lines.append(f"### {r['id']} · {r.get('category','')} · row-mean {r['_row_mean']:.3f}")
        lines.append(f"- Q: {r['user_input']}")
        scores = "  ".join(f"{c}={r[c]:.2f}" if pd.notna(r[c]) else f"{c}=NaN" for c in present)
        lines.append(f"- scores: {scores}")
        lines.append(f"- answer: {str(r['response'])[:300]}")
        lines.append("")
    lines.append("---")
    lines.append("_Longitudinal record: append each week's run below this line so W6 can be compared to W5._")
    lines.append("")
    SCORECARD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["generate", "score", "all"], default="all")
    args = ap.parse_args()
    EVALS_DIR.mkdir(exist_ok=True)
    settings = Settings.from_env()
    if args.phase in ("generate", "all"):
        phase_generate(settings)
    if args.phase in ("score", "all"):
        phase_score(settings)


if __name__ == "__main__":
    main()
