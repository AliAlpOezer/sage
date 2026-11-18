from itertools import pairwise

from sage.adapters.chunkers import RecursiveChunker
from sage.config import Settings
from sage.graph.schema import CHUNK, PAGE, SECTION, SYMBOL
from sage.graph.structural import build_structure
from sage.models import Page

AGENTS = Page(
    url="https://x/docs/agents.md",
    title="Agents",
    markdown=(
        "> index note\n\n"
        "# Agents\n\nUse `create_agent`. See [tools](https://x/docs/tools#a) and "
        "[tools again](https://x/docs/tools), [self](https://x/docs/agents), [out](https://y/z).\n\n"
        "## Loop\n\n" + "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(12)) + "\n\n"
        "```python\n# a comment the chunker splits on\nagent = create_agent()\n```\n\n"
        "## Loop\n\nSame title twice, mentions `create_agent` and `ToolMessage`.\n"
    ),
)
TOOLS = Page(
    url="https://x/docs/tools.md",
    title="Tools",
    markdown="# Tools\n\nBack to [agents](/docs/agents). `ToolMessage` carries results.\n",
)
PAGES = [AGENTS, TOOLS]


def _chunker() -> RecursiveChunker:
    return RecursiveChunker(Settings(chunk_max_chars=600, chunk_overlap_chars=80))


def _edges(structure, type_: str) -> set[tuple[str, str]]:
    return {(e.source, e.target) for e in structure.edges if e.type.type == type_}


def test_graph_chunks_are_exactly_the_vector_arms_chunks():
    structure = build_structure(PAGES, _chunker())

    for page in PAGES:
        graph_chunks = [n for n in structure.nodes if n.type is CHUNK and n.props["source_url"] == page.url]
        expected = _chunker().chunk(page)
        assert [n.key for n in graph_chunks] == [c.id for c in expected]
        assert [n.props["text"] for n in graph_chunks] == [c.text for c in expected]
        assert [n.props["position"] for n in graph_chunks] == list(range(len(expected)))


def test_every_chunk_hangs_off_a_section_and_every_section_off_its_page():
    structure = build_structure(PAGES, _chunker())
    chunk_keys = {n.key for n in structure.nodes if n.type is CHUNK}
    section_keys = {n.key for n in structure.nodes if n.type is SECTION}

    assert {target for _, target in _edges(structure, "HAS_CHUNK")} == chunk_keys
    assert {target for _, target in _edges(structure, "HAS_SECTION")} == section_keys


def test_sections_with_the_same_title_stay_distinct():
    structure = build_structure(PAGES, _chunker())
    loops = [n for n in structure.nodes if n.type is SECTION and n.props["title"] == "Loop"]

    assert len(loops) == 2
    assert {n.props["path"] for n in loops} == {"Agents > Loop"}


def test_next_chains_a_pages_chunks_in_order_and_never_crosses_pages():
    structure = build_structure(PAGES, _chunker())
    order = [n.key for n in structure.nodes if n.type is CHUNK and n.props["source_url"] == AGENTS.url]

    assert _edges(structure, "NEXT") == set(pairwise(order))


def test_links_resolve_to_snapshot_pages_only_and_are_counted():
    structure = build_structure(PAGES, _chunker())
    links = {(e.source, e.target): e.props["count"] for e in structure.edges if e.type.type == "LINKS_TO"}

    assert links == {(AGENTS.url, TOOLS.url): 2, (TOOLS.url, AGENTS.url): 1}


def test_a_symbol_is_one_node_shared_by_the_chunks_that_mention_it():
    structure = build_structure(PAGES, _chunker())
    symbol_names = {n.key for n in structure.nodes if n.type is SYMBOL}
    mentions = _edges(structure, "MENTIONS")
    pages_mentioning = {
        next(n.props["source_url"] for n in structure.nodes if n.type is CHUNK and n.key == chunk)
        for chunk, name in mentions
        if name == "ToolMessage"
    }

    assert symbol_names == {"create_agent", "ToolMessage"}
    assert pages_mentioning == {AGENTS.url, TOOLS.url}


def test_same_pages_give_the_same_records():
    assert build_structure(PAGES, _chunker()) == build_structure(PAGES, _chunker())


def test_one_page_node_per_page():
    structure = build_structure(PAGES, _chunker())

    assert {n.key for n in structure.nodes if n.type is PAGE} == {AGENTS.url, TOOLS.url}
