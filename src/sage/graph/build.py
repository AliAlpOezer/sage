"""Build the structural graph from a frozen snapshot: parse -> embed -> merge -> prune.

Repeatable: every node and edge is merged by key and stamped with this run's build
id; what an earlier build left behind is pruned only after this one fully succeeded,
so a failed run never leaves the graph smaller than before. Chunks that already carry
an embedding from the same model are not embedded again.

    SAGE_SNAPSHOT=langchain-2026-11-16 uv run python -m sage.graph.build
"""

import asyncio
from datetime import UTC, datetime
from itertools import batched

from sage.config import Settings
from sage.factory import make_chunker, make_embedder, make_graph_store
from sage.graph.schema import BUILD, CHUNK, EMBEDDING, EMBEDDING_MODEL, STRUCTURAL, Node
from sage.graph.structural import build_structure
from sage.ports import Chunker, Embedder, GraphStore
from sage.snapshot import load_snapshot, read_manifest

# Chunks embedded and written per round; bounds memory (a vector is ~50 KB as floats).
EMBED_BATCH = 256


async def build(
    settings: Settings, store: GraphStore, chunker: Chunker, embedder: Embedder, build_id: str
) -> dict[str, int]:
    """Bring `store`'s structural graph in line with `settings.snapshot`; returns counts."""
    if not settings.snapshot:
        raise ValueError(
            "the graph is built only from a frozen snapshot (graph.md invariant 4): set SAGE_SNAPSHOT"
        )
    manifest = read_manifest(settings.snapshot)
    structure = build_structure(load_snapshot(settings.snapshot), chunker)
    chunks = [n for n in structure.nodes if n.type is CHUNK]
    others = [n for n in structure.nodes if n.type is not CHUNK]
    model = settings.embedding_model

    store.ensure_constraints()
    store.merge_nodes(others, build_id)

    embedded = store.keys(CHUNK, {EMBEDDING_MODEL: model})
    fresh = [n for n in chunks if n.key not in embedded]
    store.merge_nodes([n for n in chunks if n.key in embedded], build_id)
    for round_, batch in enumerate(batched(fresh, EMBED_BATCH)):
        vectors = await embedder.embed([n.props["text"] for n in batch])
        if round_ == 0:
            store.ensure_vector_index(len(vectors[0]))
        store.merge_nodes(
            [
                Node(CHUNK, n.key, {**n.props, EMBEDDING: list(vector), EMBEDDING_MODEL: model})
                for n, vector in zip(batch, vectors, strict=True)
            ],
            build_id,
        )

    store.merge_edges(structure.edges, build_id)
    store.merge_nodes(
        [
            Node(
                BUILD,
                STRUCTURAL,
                {
                    "snapshot": manifest.name,
                    "snapshot_id": manifest.id,
                    EMBEDDING_MODEL: model,
                    "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
                },
            )
        ],
        build_id,
    )
    pruned = store.prune(STRUCTURAL, build_id)
    return {
        "nodes": len(structure.nodes),
        "edges": len(structure.edges),
        "chunks": len(chunks),
        "embedded": len(fresh),
        "pruned": pruned,
    }


def main() -> None:
    settings = Settings.from_env()
    build_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    counts = asyncio.run(
        build(settings, make_graph_store(settings), make_chunker(settings), make_embedder(settings), build_id)
    )
    print(
        f"build {build_id} from snapshot {settings.snapshot}: {counts['nodes']} nodes, "
        f"{counts['edges']} edges; embedded {counts['embedded']} of {counts['chunks']} chunks, "
        f"pruned {counts['pruned']} stale items"
    )


if __name__ == "__main__":
    main()
