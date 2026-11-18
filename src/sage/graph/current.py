"""Which build a graph namespace holds, and whether a strategy may answer from it.

Every graph strategy calls `check_build` before its first query, so a graph built from
another snapshot or embedding model is refused instead of being scored as if it were
this corpus (graph.md G9, invariant 3).
"""

from sage.config import Settings
from sage.graph.schema import BUILD, EMBEDDING_MODEL, STRUCTURAL
from sage.ports import EmptyIndex, GraphStore

BUILD_QUERY = (
    f"MATCH (b:`{BUILD.label}`:`{BUILD.namespace}` {{`{BUILD.key}`: $namespace}}) "
    f"RETURN b.snapshot AS snapshot, b.snapshot_id AS snapshot_id, b.`{EMBEDDING_MODEL}` AS embedding_model"
)


class StaleGraph(RuntimeError):
    """The graph was built from another snapshot or embedding model than the settings name."""


def check_build(
    store: GraphStore,
    settings: Settings,
    *,
    embeds_questions: bool,
    namespace: str = STRUCTURAL,
) -> None:
    """Raise unless `namespace` holds a build of `settings.snapshot`.

    `embeds_questions`: the strategy compares question embeddings with the graph's,
    so the build's embedding model must also be the configured one.
    """
    rows = store.read(BUILD_QUERY, {"namespace": namespace})
    if not rows:
        raise EmptyIndex(
            "the structural graph is not built - run: SAGE_SNAPSHOT=<name> uv run python -m sage.graph.build"
        )
    build = rows[0]
    if settings.snapshot and build["snapshot"] != settings.snapshot:
        raise StaleGraph(
            f"the graph was built from snapshot {build['snapshot']!r}, not {settings.snapshot!r}: "
            "rebuild it with sage.graph.build"
        )
    if embeds_questions and build["embedding_model"] != settings.embedding_model:
        raise StaleGraph(
            f"the graph's chunks were embedded with {build['embedding_model']!r}, but questions would "
            f"be embedded with {settings.embedding_model!r}: rebuild the graph or change the model"
        )
