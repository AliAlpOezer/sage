"""Bench candidate free judges on 2 samples: latency + do all 4 metrics land?

Picks the free judge for the baseline. Run:
    uv run python -m sage.evals.bench_judges
"""

import time

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig

from sage import openrouter
from sage.config import Settings
from sage.evals.judge import default_metrics

CANDIDATES = [
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

SAMPLES = [
    SingleTurnSample(
        user_input="What does create_agent return?",
        response="create_agent returns a compiled LangGraph graph you invoke to run the agent.",
        retrieved_contexts=[
            "create_agent() builds and returns a compiled graph. Call .invoke() on it to run the agent loop."
        ],
        reference="It returns a compiled graph (a runnable) that you invoke to execute the agent.",
    ),
    SingleTurnSample(
        user_input="What is the default temperature for ChatOpenAI?",
        response="The default temperature is 1.5 and it cannot be changed.",
        retrieved_contexts=[
            "ChatOpenAI accepts a temperature parameter controlling randomness; pass it at init."
        ],
        reference="The temperature is configurable at init; the OpenAI default is 0.7.",
    ),
]


def main() -> None:
    s = Settings.from_env()
    emb = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model=s.embedding_model,
            check_embedding_ctx_length=False,
            **openrouter.openai_kwargs(s, timeout=60),
        )
    )
    dataset = EvaluationDataset(samples=SAMPLES)
    # Serial: free tier caps at 8 req/min per model, so max_workers=1 keeps us under it.
    rc = RunConfig(max_workers=1, timeout=120, max_retries=4, max_wait=40)

    for model in CANDIDATES:
        print(f"\n{'='*70}\nJUDGE: {model}")
        llm = LangchainLLMWrapper(
            ChatOpenAI(
                model=model,
                **openrouter.openai_kwargs(s, timeout=90),
                temperature=0.0,
                timeout=90,
                max_retries=2,
            )
        )
        t0 = time.perf_counter()
        try:
            result = evaluate(
                dataset=dataset,
                metrics=default_metrics(),
                llm=llm,
                embeddings=emb,
                run_config=rc,
            )
            dt = time.perf_counter() - t0
            df = result.to_pandas()
            metric_cols = [
                c
                for c in df.columns
                if c not in ("user_input", "retrieved_contexts", "response", "reference")
            ]
            nans = int(df[metric_cols].isna().sum().sum())
            total = len(df) * len(metric_cols)
            print(f"  elapsed={dt:5.1f}s  NaN cells={nans}/{total}")
            means = {c: round(float(df[c].mean()), 3) for c in metric_cols}
            print(f"  means={means}")
        except Exception as e:  # noqa: BLE001
            dt = time.perf_counter() - t0
            print(f"  FAILED after {dt:5.1f}s: {type(e).__name__}: {str(e)[:160]}")


if __name__ == "__main__":
    main()
