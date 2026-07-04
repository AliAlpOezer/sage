"""Executable spec for the hand-written RecursiveChunker.

These tests skip while chunk() raises NotImplementedError. Once you implement
it, they become the judge: uv run python -m pytest tests/test_chunker.py -v

Test settings use small sizes (max 200 chars, overlap 40) so cases stay readable.
"""

import pytest

from sage.adapters.chunkers import RecursiveChunker
from sage.config import Settings
from sage.models import Chunk, Page

MAX = 200
OVERLAP = 40

URL = "https://docs.langchain.com/oss/python/example.md"


def page(markdown: str) -> Page:
    return Page(url=URL, title="Example", markdown=markdown)


@pytest.fixture
def chunker() -> RecursiveChunker:
    instance = RecursiveChunker(Settings(chunk_max_chars=MAX, chunk_overlap_chars=OVERLAP))
    try:
        instance.chunk(page("probe"))
    except NotImplementedError:
        pytest.skip("chunker not implemented yet — that's your job")
    return instance


def test_empty_page_yields_no_chunks(chunker):
    assert chunker.chunk(page("")) == []
    assert chunker.chunk(page("   \n\n  \n")) == []


def test_short_page_yields_one_chunk_with_correct_fields(chunker):
    chunks = chunker.chunk(page("LangChain is a framework for LLM apps."))
    assert len(chunks) == 1
    (c,) = chunks
    assert "LangChain is a framework for LLM apps." in c.text
    assert c.source_url == URL
    assert c.title == "Example"
    assert c.position == 0
    assert c.id == Chunk.make_id(URL, c.text)


def test_sections_split_at_headings_not_merged(chunker):
    md = "## Install\nRun pip install.\n\n## Usage\nImport and call it."
    chunks = chunker.chunk(page(md))
    assert len(chunks) == 2
    assert "Install" in chunks[0].text and "pip install" in chunks[0].text
    assert "Usage" in chunks[1].text and "Import and call" in chunks[1].text


def test_every_chunk_respects_max_chars(chunker):
    sections = [f"## Section {i}\n" + ("word " * 100).strip() for i in range(5)]
    chunks = chunker.chunk(page("\n\n".join(sections)))
    assert len(chunks) > 5  # 500+ char sections must have been split further
    for c in chunks:
        assert len(c.text) <= MAX, f"chunk {c.position} has {len(c.text)} chars"


def test_positions_are_sequential_document_order(chunker):
    md = "\n\n".join(f"## S{i}\ncontent {i}" for i in range(4))
    chunks = chunker.chunk(page(md))
    assert [c.position for c in chunks] == list(range(len(chunks)))
    assert "S0" in chunks[0].text
    assert "S3" in chunks[-1].text


def test_huge_single_paragraph_is_hard_split_with_overlap(chunker):
    text = "abcdefghij" * 100  # 1000 chars, no whitespace to split on
    chunks = chunker.chunk(page(text))
    assert len(chunks) >= 5
    for c in chunks:
        assert len(c.text) <= MAX
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.text[:OVERLAP] == prev.text[-OVERLAP:], (
            "consecutive hard-split pieces must overlap by overlap_chars"
        )


def test_no_blank_or_whitespace_chunks(chunker):
    md = "## A\n\n\n\ntext\n\n\n\n\n\n## B\n\nmore text\n\n\n"
    for c in chunker.chunk(page(md)):
        assert c.text.strip(), "blank chunk emitted"


def test_unicode_survives(chunker):
    chunks = chunker.chunk(page("naïve café — emoji 🚀 and ümlauts"))
    assert any("🚀" in c.text for c in chunks)
