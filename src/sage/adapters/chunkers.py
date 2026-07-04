"""Chunker adapters. The recursive chunker is HAND-WRITTEN (sprint Day 24/25
protocol: own every retrieval decision).

The executable spec lives in tests/test_chunker.py — the tests skip until this
is implemented, then judge the implementation:

    uv run python -m pytest tests/test_chunker.py -v
"""

from sage.config import Settings
from sage.factory import register_chunker
from sage.models import Chunk, Page


@register_chunker("recursive")
class RecursiveChunker:
    def __init__(self, settings: Settings):
        self.max_chars = settings.chunk_max_chars
        self.overlap_chars = settings.chunk_overlap_chars

    def chunk(self, page: Page) -> list[Chunk]:
        raise NotImplementedError("Day 25: write me by hand — spec in tests/test_chunker.py")
