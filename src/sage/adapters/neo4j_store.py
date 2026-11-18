"""GraphStore adapter: Neo4j over the official driver. The only module importing `neo4j`.

Labels, relationship types and property keys come from `sage.graph.schema`, never
from data, so they are safe to place in query text; every value travels as a parameter.
"""

import atexit
from collections.abc import Mapping, Sequence
from itertools import batched, groupby
from typing import Any

import certifi
from neo4j import Driver, GraphDatabase, Query, RoutingControl, TrustCustomCAs
from neo4j.exceptions import AuthError, ClientError, ServiceUnavailable

from sage.config import Settings
from sage.factory import register_graph_store
from sage.graph.schema import (
    CHUNK,
    CHUNK_VECTOR_INDEX,
    EMBEDDING,
    NODE_TYPES,
    Edge,
    Node,
    NodeType,
)
from sage.ports import GraphQueryError, GraphUnavailable

# Rows per write transaction. A chunk row carries its embedding (about 1,500 floats),
# so a batch stays in the low megabytes.
WRITE_BATCH = 200
PRUNE_BATCH = 1000

_UNREACHABLE = (
    "cannot reach Neo4j at {uri} ({error}). An AuraDB Free instance pauses after 3 days "
    "idle: resume it at https://console.neo4j.io, wait until it shows Running, then retry."
)


def connect(settings: Settings) -> Driver:
    """A driver for `settings.neo4j_uri`, verifying a `+s` server against certifi's CAs.

    Left to itself the driver trusts the operating system's store, and Python on
    Windows sees only the roots Windows has already downloaded: AuraDB's root is
    often not among them, so the handshake fails on a valid certificate. certifi is
    the bundle every other HTTPS call here already relies on.
    """
    auth = (settings.neo4j_username, settings.neo4j_password)
    scheme, _, rest = settings.neo4j_uri.partition("://")
    if not scheme.endswith("+s"):
        return GraphDatabase.driver(settings.neo4j_uri, auth=auth)
    return GraphDatabase.driver(
        f"{scheme.removesuffix('+s')}://{rest}",
        auth=auth,
        encrypted=True,
        trusted_certificates=TrustCustomCAs(certifi.where()),
    )


def merge_nodes_query(node_type: NodeType) -> str:
    return (
        "UNWIND $rows AS row "
        f"MERGE (n:`{node_type.label}` {{`{node_type.key}`: row.key}}) "
        f"SET n:`{node_type.namespace}`, n += row.props, n.build_id = $build_id"
    )


def merge_edges_query(edge: Edge) -> str:
    source, target = edge.type.source, edge.type.target
    return (
        "UNWIND $rows AS row "
        f"MATCH (a:`{source.label}` {{`{source.key}`: row.source}}) "
        f"MATCH (b:`{target.label}` {{`{target.key}`: row.target}}) "
        f"MERGE (a)-[r:`{edge.type.type}`]->(b) "
        "SET r += row.props, r.build_id = $build_id"
    )


@register_graph_store("neo4j")
class Neo4jStore:
    def __init__(self, settings: Settings):
        if not (settings.neo4j_uri and settings.neo4j_password):
            raise GraphUnavailable("Neo4j is not configured: set NEO4J_URI, NEO4J_USERNAME and NEO4J_PASSWORD in .env")
        self.uri = settings.neo4j_uri
        self.database = settings.neo4j_database or None
        self.timeout = settings.graph_query_timeout
        self.driver = connect(settings)
        atexit.register(self.driver.close)

    def _run(self, query: str, params: Mapping[str, Any] | None, routing: RoutingControl) -> list[dict[str, Any]]:
        timeout = self.timeout if routing is RoutingControl.READ else None
        try:
            records, _, _ = self.driver.execute_query(
                Query(query, timeout=timeout),  # type: ignore[arg-type]  # text is built from the schema
                parameters_=dict(params or {}),
                routing_=routing,
                database_=self.database,
            )
        except AuthError as exc:
            raise GraphUnavailable(f"Neo4j refused the credentials for {self.uri}: {exc.message}") from exc
        except (ServiceUnavailable, OSError) as exc:
            raise GraphUnavailable(_UNREACHABLE.format(uri=self.uri, error=type(exc).__name__)) from exc
        except ClientError as exc:
            raise GraphQueryError(exc.code or "Neo.ClientError", exc.message or str(exc)) from exc
        return [record.data() for record in records]

    def _write(self, query: str, **params: Any) -> list[dict[str, Any]]:
        return self._run(query, params, RoutingControl.WRITE)

    def ensure_constraints(self) -> None:
        for node_type in NODE_TYPES:
            name = f"{node_type.label.lower()}_{node_type.key}"
            self._write(
                f"CREATE CONSTRAINT `{name}` IF NOT EXISTS "
                f"FOR (n:`{node_type.label}`) REQUIRE n.`{node_type.key}` IS UNIQUE"
            )

    def ensure_vector_index(self, dimension: int) -> None:
        existing = self.read(
            "SHOW VECTOR INDEXES YIELD name, options WHERE name = $name RETURN options",
            {"name": CHUNK_VECTOR_INDEX},
        )
        if existing:
            have = existing[0]["options"]["indexConfig"]["vector.dimensions"]
            if have != dimension:
                raise RuntimeError(
                    f"vector index {CHUNK_VECTOR_INDEX} holds {have}-dimensional vectors but the "
                    f"embedder returns {dimension}: drop the index and rebuild the graph"
                )
            return
        self._write(
            f"CREATE VECTOR INDEX `{CHUNK_VECTOR_INDEX}` IF NOT EXISTS "
            f"FOR (c:`{CHUNK.label}`) ON (c.`{EMBEDDING}`) "
            "OPTIONS {indexConfig: {`vector.dimensions`: $dimension, "
            "`vector.similarity_function`: 'cosine'}}",
            dimension=int(dimension),
        )

    def keys(self, node_type: NodeType, where: Mapping[str, Any]) -> set[str]:
        rows = self.read(
            f"MATCH (n:`{node_type.label}`) "
            "WHERE all(name IN keys($where) WHERE n[name] = $where[name]) "
            f"RETURN n.`{node_type.key}` AS key",
            {"where": dict(where)},
        )
        return {row["key"] for row in rows}

    def merge_nodes(self, nodes: Sequence[Node], build_id: str) -> None:
        by_type = sorted(nodes, key=lambda n: n.type.label)
        for _, group in groupby(by_type, key=lambda n: n.type.label):
            for batch in batched(group, WRITE_BATCH):
                rows = [{"key": n.key, "props": dict(n.props)} for n in batch]
                self._write(merge_nodes_query(batch[0].type), rows=rows, build_id=build_id)

    def merge_edges(self, edges: Sequence[Edge], build_id: str) -> None:
        def kind(e: Edge) -> tuple[str, str, str]:
            return (e.type.type, e.type.source.label, e.type.target.label)

        for _, group in groupby(sorted(edges, key=kind), key=kind):
            for batch in batched(group, WRITE_BATCH):
                rows = [{"source": e.source, "target": e.target, "props": dict(e.props)} for e in batch]
                written = self._write(
                    merge_edges_query(batch[0]) + " RETURN count(r) AS written", rows=rows, build_id=build_id
                )[0]["written"]
                if written != len(rows):
                    raise RuntimeError(
                        f"{len(rows) - written} {batch[0].type.type} edges name a node that does not exist"
                    )

    def prune(self, namespace: str, build_id: str) -> int:
        stale_edges = (
            f"MATCH (:`{namespace}`)-[r]->(:`{namespace}`) WHERE r.build_id <> $build_id "
            "WITH r LIMIT $batch DELETE r RETURN count(*) AS deleted"
        )
        stale_nodes = (
            f"MATCH (n:`{namespace}`) WHERE n.build_id <> $build_id "
            "WITH n LIMIT $batch DETACH DELETE n RETURN count(*) AS deleted"
        )
        total = 0
        for query in (stale_edges, stale_nodes):
            while deleted := self._write(query, build_id=build_id, batch=PRUNE_BATCH)[0]["deleted"]:
                total += deleted
        return total

    def read(self, cypher: str, params: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._run(cypher, params, RoutingControl.READ)
