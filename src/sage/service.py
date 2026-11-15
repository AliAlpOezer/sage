"""Programmatic query loop shared by the CLI and the HTTP API.

`answer()` runs the configured RetrievalStrategy (`settings.strategy`), arranges its
chunks, and generates, returning the text plus the structured source list (numbered
to match the inline [n] citations the generator emits). Each source carries its chunk
`text` so the UI's inspector panel can show what was actually retrieved, and the
answer names the strategy that produced it.
"""

from dataclasses import dataclass

from sage.assembly import arrange
from sage.config import Settings
from sage.factory import make_generator, make_strategy
from sage.ports import EmptyIndex

__all__ = ["Answer", "EmptyIndex", "Source", "answer"]


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
    strategy: str  # the RetrievalStrategy that produced the context


def answer(question: str, k: int | None = None, settings: Settings | None = None) -> Answer:
    settings = settings or Settings.from_env()
    k = k or settings.top_k
    strategy = make_strategy(settings)
    generator = make_generator(settings)

    hits = strategy.retrieve(question, k)
    context = arrange(hits, order=settings.assembly_order)
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
    return Answer(answer=text, sources=sources, strategy=settings.strategy)
