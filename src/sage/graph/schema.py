"""The graph schema: node labels, their keys, relationship types, namespaces.

Builders and strategies import these names; no label or relationship type is spelled
out anywhere else. A namespace is a second label on every node of one graph flavor
(structural now, LLM-extracted later). Flavors share one database but no query
crosses a namespace, so a result can be attributed to one of them (graph.md G11).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NodeType:
    label: str
    key: str  # the property that identifies a node; unique per label
    namespace: str


@dataclass(frozen=True)
class EdgeType:
    type: str
    source: NodeType
    target: NodeType


@dataclass(frozen=True)
class Node:
    type: NodeType
    key: str
    props: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    type: EdgeType
    source: str  # key of the source node
    target: str  # key of the target node
    props: Mapping[str, Any] = field(default_factory=dict)


STRUCTURAL = "Structural"

PAGE = NodeType("Page", "url", STRUCTURAL)
SECTION = NodeType("Section", "id", STRUCTURAL)
CHUNK = NodeType("Chunk", "id", STRUCTURAL)
SYMBOL = NodeType("Symbol", "name", STRUCTURAL)
# One per namespace: which snapshot and embedding model the current build came from.
BUILD = NodeType("Build", "namespace", STRUCTURAL)

PAGE_HAS_SECTION = EdgeType("HAS_SECTION", PAGE, SECTION)
SECTION_HAS_SECTION = EdgeType("HAS_SECTION", SECTION, SECTION)
HAS_CHUNK = EdgeType("HAS_CHUNK", SECTION, CHUNK)
NEXT = EdgeType("NEXT", CHUNK, CHUNK)
LINKS_TO = EdgeType("LINKS_TO", PAGE, PAGE)
MENTIONS = EdgeType("MENTIONS", CHUNK, SYMBOL)

NODE_TYPES = (PAGE, SECTION, CHUNK, SYMBOL, BUILD)

# Chunk.embedding carries the vector a graph query seeds from (graph.md G5).
EMBEDDING = "embedding"
EMBEDDING_MODEL = "embedding_model"
CHUNK_VECTOR_INDEX = "chunk_embedding"
