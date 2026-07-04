"""Query loop: embed question -> top-k -> assemble context -> generate.

    uv run python -m sage.ask "How do I use create_agent?"
    uv run python -m sage.ask -k 8 "..."
"""

import argparse
import asyncio

from sage.assembly import arrange
from sage.config import Settings
from sage.factory import make_embedder, make_generator, make_vector_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the LangChain docs a question.")
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=None, help="chunks to retrieve (default: SAGE_TOP_K)")
    args = parser.parse_args()

    settings = Settings.from_env()
    k = args.k or settings.top_k
    embedder = make_embedder(settings)
    store = make_vector_store(settings)
    generator = make_generator(settings)

    if store.count() == 0:
        raise SystemExit("vector store is empty — run: uv run python -m sage.ingest")

    query_vector = asyncio.run(embedder.embed([args.question]))[0]
    hits = store.search(query_vector, k)
    context = arrange(hits)

    answer = generator.generate(args.question, context)

    print(answer)
    print("\nSources:")
    for i, scored in enumerate(context, start=1):
        print(f"  [{i}] {scored.chunk.title} — {scored.chunk.source_url}  (score {scored.score:.3f})")


if __name__ == "__main__":
    main()
