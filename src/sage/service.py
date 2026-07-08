"""Programmatic query loop shared by the CLI and the HTTP API.

`ask.py` printed its result; the UI needs it as data. This extracts the
embed -> top-k -> assemble -> generate loop into `answer()`, which returns the
generated text plus the structured source list (numbered to match the inline
[n] citations the generator emits). Each source carries its chunk `text` so the
UI's inspector panel can show what was actually retrieved.
"""

import asyncio
from dataclasses import dataclass

from sage.assembly import arrange
from sage.config import Settings
from sage.factory import make_embedder, make_generator, make_vector_store


@dataclass(frozen=True)
class Source:
    n: int  # matches the inline [n] citation in the answer
    title: str
    url: str
    score: float
    text: str


@dataclass(frozen=True)
class Answer:
    answer: str
    sources: list[Source]


class EmptyIndex(RuntimeError):
    """Raised when the vector store has no vectors — ingest hasn't been run."""


def answer(question: str, k: int | None = None, settings: Settings | None = None) -> Answer:
    settings = settings or Settings.from_env()
    k = k or settings.top_k
    embedder = make_embedder(settings)
    store = make_vector_store(settings)
    generator = make_generator(settings)

    if store.count() == 0:
        raise EmptyIndex("vector store is empty — run: uv run python -m sage.ingest")

    query_vector = asyncio.run(embedder.embed([question]))[0]
    hits = store.search(query_vector, k)
    context = arrange(hits)
    text = generator.generate(question, context)

    sources = [
        Source(
            n=i,
            title=s.chunk.title,
            url=s.chunk.source_url,
            score=s.score,
            text=s.chunk.text,
        )
        for i, s in enumerate(context, start=1)
    ]
    return Answer(answer=text, sources=sources)
