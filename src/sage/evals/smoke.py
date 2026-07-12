"""Day-29 smoke test: run RAGAS on 3 hand-made samples to see the mechanics.

Not a pytest (needs live OpenRouter calls). Run:
    uv run python -m sage.evals.smoke
"""

from ragas import EvaluationDataset, SingleTurnSample, evaluate

from sage.evals.judge import build_judge, default_metrics, default_run_config

# Three hand-made (question, answer, contexts, reference) samples. Deliberately
# one good, one hallucinated, one under-retrieved — so we can see each metric move.
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
        response="The default temperature is 1.5 and it cannot be changed.",  # hallucinated
        retrieved_contexts=[
            "ChatOpenAI accepts a temperature parameter controlling randomness; pass it at init."
        ],
        reference="The temperature is configurable at init; the OpenAI default is 0.7.",
    ),
    SingleTurnSample(
        user_input="How do I stream tokens from a chat model?",
        response="Use the .stream() method to iterate over message chunks as they arrive.",
        retrieved_contexts=[
            "LangChain vector stores support similarity_search over embeddings."  # off-topic → low recall/precision
        ],
        reference="Call .stream() (or .astream()) on the model to yield chunks incrementally.",
    ),
]


def main() -> None:
    llm, emb = build_judge()
    dataset = EvaluationDataset(samples=SAMPLES)
    result = evaluate(
        dataset=dataset,
        metrics=default_metrics(),
        llm=llm,
        embeddings=emb,
        run_config=default_run_config(),
    )
    print("\n=== RAGAS smoke result (3 samples) ===")
    print(result)
    df = result.to_pandas()
    print("\nper-sample:")
    print(df.to_string())


if __name__ == "__main__":
    main()
