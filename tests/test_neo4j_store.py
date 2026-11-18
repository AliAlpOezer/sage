import pytest

from sage import factory
from sage.adapters.neo4j_store import merge_edges_query, merge_nodes_query
from sage.config import Settings
from sage.graph.schema import CHUNK, HAS_CHUNK, Edge
from sage.ports import GraphUnavailable


def test_nodes_merge_on_the_key_and_take_the_namespace_label():
    query = merge_nodes_query(CHUNK)

    assert "MERGE (n:`Chunk` {`id`: row.key})" in query
    assert "SET n:`Structural`, n += row.props, n.build_id = $build_id" in query


def test_edges_match_both_ends_by_their_own_keys():
    query = merge_edges_query(Edge(HAS_CHUNK, "s1", "c1"))

    assert "MATCH (a:`Section` {`id`: row.source})" in query
    assert "MATCH (b:`Chunk` {`id`: row.target})" in query
    assert "MERGE (a)-[r:`HAS_CHUNK`]->(b)" in query


def test_an_unconfigured_store_says_which_settings_are_missing():
    with pytest.raises(GraphUnavailable, match="NEO4J_URI"):
        factory.make_graph_store(Settings(neo4j_uri="", neo4j_password=""))
