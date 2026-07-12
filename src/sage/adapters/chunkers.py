"""Chunker adapters. The recursive chunker is HAND-WRITTEN (sprint Day 24/25
protocol: own every retrieval decision).

The executable spec lives in tests/test_chunker.py — the tests skip until this
is implemented, then judge the implementation:

    uv run python -m pytest tests/test_chunker.py -v
"""
import re

from sage.config import Settings
from sage.factory import register_chunker
from sage.models import Chunk, Page


@register_chunker("recursive")
class RecursiveChunker:
    def __init__(self, settings: Settings):
        self.max_chars = settings.chunk_max_chars
        self.overlap_chars = settings.chunk_overlap_chars

    def chunk(self, page: Page) -> list[Chunk]:
        sections = re.split(r'^(?=#{1,6}\s)', page.markdown, flags=re.MULTILINE)

        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # step 2: Section fits in one chunk
            if len(section) <= self.max_chars:
                chunks.append(Chunk(
                    id=Chunk.make_id(page.url, section),
                    text=section,
                    source_url=page.url,
                    title=page.title,
                    position=len(chunks),
                ))
                continue
            
            #step 3: Section is too long, split into paragraphs
            paragraphs = re.split(r'\n\n', section)
            current_chunk_parts = []
            current_chunk_length = 0

            for para in paragraphs:
                para =para.strip()
                if not para:
                    continue

                if len(para) > self.max_chars:
                    # If a paragraph is too long, split it into smaller parts
                    if current_chunk_parts:
                        chunk_text = '\n\n'.join(current_chunk_parts)
                        chunks.append(Chunk(
                            id=Chunk.make_id(page.url, chunk_text),
                            text=chunk_text,
                            source_url=page.url,
                            title=page.title,
                            position=len(chunks),
                        ))
                        current_chunk_parts = []
                        current_chunk_length = 0
                    
                    # hard split with overlap
                    stride = self.max_chars - self.overlap_chars
                    for i in range(0, len(para), stride):
                        piece = para[i:i+self.max_chars]
                        chunks.append(Chunk(
                            id=Chunk.make_id(page.url, piece),
                            text=piece,
                            source_url=page.url,
                            title=page.title,
                            position=len(chunks),  # Set position at construction
                        ))
                        if i + self.max_chars >= len(para):
                            break
                    continue

                #step 5: Greedy packing - check if adding this paragraph would exceed the max_chars limit

                separator_length = len("\n\n") if current_chunk_parts else 0
                if current_chunk_length + len(para) + separator_length <= self.max_chars:
                    current_chunk_parts.append(para)
                    current_chunk_length += len(para) + separator_length
                else:
                    # Finalize the current chunk and start a new one
                    chunk_text = '\n\n'.join(current_chunk_parts)
                    chunks.append(Chunk(
                        id=Chunk.make_id(page.url, chunk_text),
                        text=chunk_text,
                        source_url=page.url,
                        title=page.title,
                        position=len(chunks),
                    ))
                    current_chunk_parts = [para]
                    current_chunk_length = len(para)

            if current_chunk_parts:
                chunk_text = '\n\n'.join(current_chunk_parts)
                chunks.append(Chunk(
                    id=Chunk.make_id(page.url, chunk_text),
                    text=chunk_text,
                    source_url=page.url,
                    title=page.title,
                    position=len(chunks),
                ))

        return chunks


@register_chunker("fixed")
class FixedChunker:
    """Naive fixed-size sliding window — structure-blind, splits mid-sentence.

    The comparison foil for the Day-32 bake-off: it ignores markdown headings and
    paragraphs entirely, so it's the "what does honoring structure actually buy?"
    control against the hand-written recursive chunker. (Not a learning artifact —
    the recursive one is; this exists only to be measured against.)
    """

    def __init__(self, settings: Settings):
        self.max_chars = settings.chunk_max_chars
        self.overlap_chars = settings.chunk_overlap_chars

    def chunk(self, page: Page) -> list[Chunk]:
        text = page.markdown.strip()
        if not text:
            return []
        stride = max(1, self.max_chars - self.overlap_chars)
        chunks: list[Chunk] = []
        for i in range(0, len(text), stride):
            piece = text[i:i + self.max_chars].strip()
            if piece:
                chunks.append(Chunk(
                    id=Chunk.make_id(page.url, piece),
                    text=piece,
                    source_url=page.url,
                    title=page.title,
                    position=len(chunks),
                ))
            if i + self.max_chars >= len(text):
                break
        return chunks