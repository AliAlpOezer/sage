"""The structural graph: what the pages' own markup says, at zero LLM cost.

    (:Page)-[:HAS_SECTION]->(:Section)-[:HAS_SECTION]->(:Section)
    (:Section)-[:HAS_CHUNK]->(:Chunk)-[:NEXT]->(:Chunk)
    (:Page)-[:LINKS_TO]->(:Page)        (:Chunk)-[:MENTIONS]->(:Symbol)

Chunks come from the same `Chunker` the vector arm uses, applied section by section,
so both arms retrieve over the same chunk texts and ids: a score difference is then
down to retrieval, not chunking. Deterministic: the same pages give the same records.
"""

import hashlib
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace

from sage.graph.markdown import (
    link_targets,
    page_key,
    parse_sections,
    resolve_link,
    symbols,
)
from sage.graph.schema import (
    CHUNK,
    HAS_CHUNK,
    LINKS_TO,
    MENTIONS,
    NEXT,
    PAGE,
    PAGE_HAS_SECTION,
    SECTION,
    SECTION_HAS_SECTION,
    SYMBOL,
    Edge,
    Node,
)
from sage.models import Page
from sage.ports import Chunker


@dataclass(frozen=True)
class Structure:
    nodes: tuple[Node, ...]  # unique per (type, key); chunks in page order
    edges: tuple[Edge, ...]  # unique per (type, source, target)


def _section_id(url: str, path: tuple[str, ...], occurrence: int) -> str:
    digest = hashlib.sha256("\n".join((url, *path, str(occurrence))).encode()).hexdigest()
    return digest[:32]


def build_structure(pages: Sequence[Page], chunker: Chunker) -> Structure:
    nodes: dict[tuple[str, str], Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}

    def add_node(node: Node) -> None:
        nodes.setdefault((node.type.label, node.key), node)

    def add_edge(edge: Edge) -> None:
        edges.setdefault((edge.type.type, edge.source, edge.target), edge)

    url_of = {page_key(page.url): page.url for page in pages}

    for page in pages:
        add_node(Node(PAGE, page.url, {"title": page.title}))

        section_ids: list[str] = []
        seen_paths: Counter[tuple[str, ...]] = Counter()
        previous_chunk: str | None = None
        position = 0
        for index, section in enumerate(parse_sections(page.markdown)):
            section_id = _section_id(page.url, section.path, seen_paths[section.path])
            seen_paths[section.path] += 1
            section_ids.append(section_id)
            add_node(
                Node(
                    SECTION,
                    section_id,
                    {
                        "title": section.title,
                        "level": section.level,
                        "path": " > ".join(section.path),
                        "position": index,
                        "page_url": page.url,
                    },
                )
            )
            if section.parent is None:
                add_edge(Edge(PAGE_HAS_SECTION, page.url, section_id))
            else:
                add_edge(Edge(SECTION_HAS_SECTION, section_ids[section.parent], section_id))

            for chunk in chunker.chunk(replace(page, markdown=section.text)):
                add_node(
                    Node(
                        CHUNK,
                        chunk.id,
                        {
                            "text": chunk.text,
                            "source_url": chunk.source_url,
                            "title": chunk.title,
                            "position": position,
                        },
                    )
                )
                position += 1
                add_edge(Edge(HAS_CHUNK, section_id, chunk.id))
                if previous_chunk is not None and previous_chunk != chunk.id:
                    add_edge(Edge(NEXT, previous_chunk, chunk.id))
                previous_chunk = chunk.id
                for name in sorted(symbols(chunk.text)):
                    add_node(Node(SYMBOL, name))
                    add_edge(Edge(MENTIONS, chunk.id, name))

        linked = Counter(
            url_of[key]
            for target in link_targets(page.markdown)
            if (key := resolve_link(page.url, target)) in url_of
        )
        for target_url, count in linked.items():
            if target_url != page.url:
                add_edge(Edge(LINKS_TO, page.url, target_url, {"count": count}))

    return Structure(nodes=tuple(nodes.values()), edges=tuple(edges.values()))
