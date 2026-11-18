import asyncio
import json
from dataclasses import replace

import pytest

from sage import snapshot
from sage.adapters.chunkers import RecursiveChunker
from sage.config import Settings
from sage.graph.build import build
from sage.graph.schema import (
    BUILD,
    CHUNK,
    EMBEDDING,
    EMBEDDING_MODEL,
    PAGE,
    STRUCTURAL,
    SYMBOL,
)
from sage.ports import GraphStore
from sage.sources import SOURCES

AGENTS_URL = "https://docs.langchain.com/oss/python/langchain/agents.md"
TOOLS_URL = "https://docs.langchain.com/oss/python/langchain/tools.md"
AGENTS_MD = (
    "# Agents\n\nUse `create_agent` with "
    "[tools](https://docs.langchain.com/oss/python/langchain/tools).\n\n## Loop\n\nThe loop.\n"
)
TOOLS_MD = "# Tools\n\n`ToolMessage` carries a result.\n"


class InMemoryGraphStore:
    """A GraphStore that keeps what it is given; `read` is not needed by the builder."""

    def __init__(self):
        self.nodes: dict[tuple[str, str], dict] = {}
        self.edges: dict[tuple[str, str, str, str, str], dict] = {}
        self.namespaces: dict[tuple[str, str], str] = {}
        self.vector_dimension: int | None = None
        self.constraints = False

    def ensure_constraints(self):
        self.constraints = True

    def ensure_vector_index(self, dimension):
        assert self.vector_dimension in (None, dimension)
        self.vector_dimension = dimension

    def keys(self, node_type, where):
        return {
            key
            for (label, key), props in self.nodes.items()
            if label == node_type.label and all(props.get(k) == v for k, v in where.items())
        }

    def merge_nodes(self, nodes, build_id):
        assert self.constraints, "constraints must exist before the first merge"
        for node in nodes:
            stored = self.nodes.setdefault((node.type.label, node.key), {})
            stored.update(node.props, build_id=build_id)
            self.namespaces[(node.type.label, node.key)] = node.type.namespace

    def merge_edges(self, edges, build_id):
        for edge in edges:
            source = (edge.type.source.label, edge.source)
            target = (edge.type.target.label, edge.target)
            assert source in self.nodes and target in self.nodes, f"dangling {edge.type.type} edge"
            self.edges.setdefault((edge.type.type, *source, *target), {}).update(edge.props, build_id=build_id)

    def prune(self, namespace, build_id):
        stale_nodes = [
            k for k, props in self.nodes.items() if self.namespaces[k] == namespace and props["build_id"] != build_id
        ]
        for key in stale_nodes:
            del self.nodes[key]
        stale_edges = [
            k
            for k, props in self.edges.items()
            if props["build_id"] != build_id or k[1:3] not in self.nodes or k[3:5] not in self.nodes
        ]
        for key in stale_edges:
            del self.edges[key]
        return len(stale_nodes) + len(stale_edges)

    def read(self, cypher, params=None):
        raise NotImplementedError

    def content(self):
        """Everything stored, minus the per-run stamps."""
        volatile = {"build_id", "built_at"}

        def strip(props):
            return {k: v for k, v in props.items() if k not in volatile}

        return (
            {k: strip(v) for k, v in self.nodes.items()},
            {k: strip(v) for k, v in self.edges.items()},
        )


class CountingEmbedder:
    def __init__(self, fail: bool = False):
        self.texts: list[str] = []
        self.fail = fail

    async def embed(self, texts):
        if self.fail:
            raise ConnectionError("quota")
        self.texts += texts
        return [[float(len(t)), 1.0] for t in texts]


def _write_snapshot(root, name: str, pages: dict[str, str]) -> None:
    entries = tuple(
        snapshot.SnapshotPage(url=url, source="langchain", sha256=snapshot._sha256(raw))
        for url, raw in pages.items()
    )
    for url, raw in pages.items():
        file = snapshot._content_file(name, url)
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(raw, encoding="utf-8")
    body = {
        "name": name,
        "id": snapshot.snapshot_id(entries),
        "created": "2026-11-16",
        "pages": [vars(e) for e in entries],
    }
    snapshot.MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (snapshot.MANIFEST_DIR / f"{name}.json").write_text(json.dumps(body), encoding="utf-8")


@pytest.fixture
def snapshots(tmp_path, monkeypatch):
    monkeypatch.setattr(snapshot, "MANIFEST_DIR", tmp_path / "manifests")
    monkeypatch.setattr(snapshot, "CONTENT_DIR", tmp_path / "content")
    _write_snapshot(tmp_path, "two-pages", {AGENTS_URL: AGENTS_MD, TOOLS_URL: TOOLS_MD})
    _write_snapshot(tmp_path, "agents-only", {AGENTS_URL: AGENTS_MD})
    return tmp_path


def _settings(name: str = "two-pages") -> Settings:
    return Settings(snapshot=name, embedding_model="test-embedder")


def _build(store, settings=None, embedder=None, build_id="b1"):
    settings = settings or _settings()
    embedder = embedder or CountingEmbedder()
    return asyncio.run(build(settings, store, RecursiveChunker(settings), embedder, build_id))


def test_the_fake_satisfies_the_port():
    assert isinstance(InMemoryGraphStore(), GraphStore)


def test_build_writes_the_structure_with_embeddings_and_provenance(snapshots):
    store = InMemoryGraphStore()

    counts = _build(store)

    chunks = [props for (label, _), props in store.nodes.items() if label == CHUNK.label]
    assert counts["chunks"] == len(chunks) == counts["embedded"]
    assert all(c[EMBEDDING] == [float(len(c["text"])), 1.0] for c in chunks)
    assert all(c[EMBEDDING_MODEL] == "test-embedder" for c in chunks)
    assert store.vector_dimension == 2
    assert (PAGE.label, TOOLS_URL) in store.nodes and (SYMBOL.label, "ToolMessage") in store.nodes
    assert ("LINKS_TO", PAGE.label, AGENTS_URL, PAGE.label, TOOLS_URL) in store.edges
    record = store.nodes[(BUILD.label, STRUCTURAL)]
    assert record["snapshot"] == "two-pages"
    assert record["snapshot_id"] == snapshot.read_manifest("two-pages").id


def test_two_builds_of_one_snapshot_leave_the_same_graph(snapshots):
    store = InMemoryGraphStore()
    _build(store, build_id="b1")
    first = store.content()

    counts = _build(store, build_id="b2")

    assert store.content() == first
    assert counts["pruned"] == 0
    assert {props["build_id"] for props in (*store.nodes.values(), *store.edges.values())} == {"b2"}


def test_a_rebuild_does_not_embed_chunks_again(snapshots):
    store = InMemoryGraphStore()
    _build(store, build_id="b1")
    embedder = CountingEmbedder()

    counts = _build(store, embedder=embedder, build_id="b2")

    assert embedder.texts == []
    assert counts["embedded"] == 0
    assert all(EMBEDDING in props for (label, _), props in store.nodes.items() if label == CHUNK.label)


def test_another_embedding_model_embeds_everything_again(snapshots):
    store = InMemoryGraphStore()
    _build(store, build_id="b1")

    counts = _build(store, settings=replace(_settings(), embedding_model="other"), build_id="b2")

    assert counts["embedded"] == counts["chunks"]


def test_a_build_from_a_smaller_snapshot_prunes_what_is_gone(snapshots):
    store = InMemoryGraphStore()
    _build(store, build_id="b1")

    counts = _build(store, settings=_settings("agents-only"), build_id="b2")

    fresh = InMemoryGraphStore()
    _build(fresh, settings=_settings("agents-only"), build_id="b2")
    assert counts["pruned"] > 0
    assert store.content() == fresh.content()
    assert (PAGE.label, TOOLS_URL) not in store.nodes


def test_a_failed_build_prunes_nothing(snapshots):
    store = InMemoryGraphStore()
    _build(store, build_id="b1")
    before = set(store.nodes)

    with pytest.raises(ConnectionError):
        _build(
            store,
            settings=replace(_settings("agents-only"), embedding_model="other"),
            embedder=CountingEmbedder(fail=True),
            build_id="b2",
        )

    assert set(store.nodes) == before


def test_build_refuses_a_live_crawl(snapshots):
    with pytest.raises(ValueError, match="frozen snapshot"):
        _build(InMemoryGraphStore(), settings=Settings())


def test_snapshot_pages_are_cleaned_like_a_live_crawl(snapshots):
    pages = snapshot.load_snapshot("two-pages")

    assert [(p.url, p.title) for p in pages] == [(AGENTS_URL, "Agents"), (TOOLS_URL, "Tools")]
    assert pages[0].markdown == SOURCES["langchain"].clean(AGENTS_MD)


def test_a_changed_snapshot_page_is_refused(snapshots):
    snapshot._content_file("two-pages", TOOLS_URL).write_text("# Tools\n\nedited\n", encoding="utf-8")

    with pytest.raises(snapshot.SnapshotError, match="no longer matches"):
        snapshot.load_snapshot("two-pages")


def test_a_missing_snapshot_page_is_refused(snapshots):
    snapshot._content_file("two-pages", TOOLS_URL).unlink()

    with pytest.raises(snapshot.SnapshotError, match="content missing"):
        snapshot.load_snapshot("two-pages")


def test_snapshot_id_ignores_page_order():
    a = snapshot.SnapshotPage(url="https://x/a.md", source="langchain", sha256="1")
    b = snapshot.SnapshotPage(url="https://x/b.md", source="langchain", sha256="2")

    assert snapshot.snapshot_id((a, b)) == snapshot.snapshot_id((b, a))
    assert snapshot.snapshot_id((a, b)) != snapshot.snapshot_id((a, replace(b, sha256="3")))
