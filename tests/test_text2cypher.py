import pytest

from sage import factory
from sage.adapters.chunkers import RecursiveChunker
from sage.adapters.text2cypher import (
    HIDDEN,
    PROPERTIES,
    SYSTEM,
    Text2CypherStrategy,
    UnsafeCypher,
    bounded,
    extract_query,
    guard,
    render,
)
from sage.config import Settings
from sage.graph.current import BUILD_QUERY, StaleGraph
from sage.graph.structural import build_structure
from sage.models import Page
from sage.ports import EmptyIndex, GraphQueryError, RetrievalStrategy

BUILD_ROW = {"snapshot": "snap", "snapshot_id": "abc", "embedding_model": "model-a"}
COUNT = "MATCH (c:Chunk) RETURN count(c) AS chunks"


class FakeGraph:
    """Serves the build check, then answers or refuses each wrapped query in turn."""

    def __init__(self, outcomes=(), build=BUILD_ROW):
        self.outcomes = list(outcomes)  # rows, or an exception to raise
        self.build = build
        self.queries: list[str] = []

    def read(self, cypher, params=None):
        if cypher == BUILD_QUERY:
            return [self.build] if self.build else []
        self.queries.append(cypher)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeChat:
    """Replies with canned queries, in order, and keeps every prompt it was sent."""

    def __init__(self):
        self.replies: list[str] = []
        self.prompts: list[tuple[str, str]] = []
        self.model = ""

    def complete(self, system, user):
        self.prompts.append((system, user))
        return self.replies.pop(0)


_GRAPH = FakeGraph()
_CHAT = FakeChat()


@factory.register_graph_store("fake-cypher-graph")
def _fake_graph(settings: Settings) -> FakeGraph:
    return _GRAPH


@factory.register_generator("fake-cypher-chat")
def _fake_chat(settings: Settings) -> FakeChat:
    _CHAT.model = settings.generation_model
    return _CHAT


@factory.register_vector_store("raising-cypher")
def _raising_store(settings: Settings):
    raise AssertionError(
        "a graph strategy must never build the vector store (graph.md invariant 1)"
    )


def _settings(**overrides) -> Settings:
    base = {
        "strategy": "text2cypher",
        "graph_store": "fake-cypher-graph",
        "neo4j_uri": "fake://text2cypher-test",
        "generator": "fake-cypher-chat",
        "generation_model": "answer-model",
        "vector_store": "raising-cypher",
        "embedding_model": "model-a",
        "snapshot": "snap",
        "text2cypher_max_rows": 3,
    }
    return Settings(**{**base, **overrides})


def _setup(replies, outcomes, build=BUILD_ROW):
    # The factory caches graph stores per connection, so reset the shared fakes in place.
    _GRAPH.__init__(outcomes, build)
    _CHAT.__init__()
    _CHAT.replies = [f"```cypher\n{r}\n```" for r in replies]
    return _GRAPH, _CHAT


# --- guard (graph.md G12) ---


@pytest.mark.parametrize(
    "query",
    [
        COUNT,
        "MATCH (c:Chunk) WHERE toLower(c.text) CONTAINS 'set up' OR c.text CONTAINS \"delete\" RETURN c.id AS id",
        "MATCH (p:Page) RETURN p.`set` AS weird // CREATE in a comment",
        "MATCH (p:Page) CALL (p) { MATCH (p)-[:LINKS_TO]->(q) RETURN count(q) AS n } RETURN p.url AS url, n",
        "MATCH (p:Page) WHERE p.url STARTS WITH 'https://' RETURN p.url AS url",
        "MATCH (p:Page) RETURN p.url AS x UNION MATCH (y:Symbol) RETURN y.name AS x",
    ],
)
def test_guard_lets_read_queries_through(query):
    guard(query)


@pytest.mark.parametrize(
    "query, reason",
    [
        ("CREATE (n:Page {url: 'x'}) RETURN n", "CREATE"),
        ("MATCH (p:Page) SET p.title = 'x' RETURN p.url AS url", "SET"),
        ("match (p:Page) detach delete p", "DETACH"),
        ("MERGE (p:Page {url: 'x'}) RETURN p.url AS url", "MERGE"),
        ("MATCH (p:Page) REMOVE p.title RETURN p.url AS url", "REMOVE"),
        ("LOAD CSV FROM 'https://x' AS row RETURN row", "LOAD"),
        ("USE system SHOW USERS", "USE"),
        ("EXPLAIN MATCH (p:Page) RETURN p.url AS url", "EXPLAIN"),
        ("CYPHER 25 MATCH (p:Page) RETURN p.url AS url", "CYPHER"),
        ("CALL db.labels() YIELD label RETURN label", "procedure"),
        (
            "CALL apoc.periodic.iterate('a', 'b', {}) YIELD batches RETURN batches",
            "procedure",
        ),
        (
            "MATCH (p:Page) CALL (p) { MATCH (p) RETURN p.url AS u } IN TRANSACTIONS RETURN u",
            "TRANSACTIONS",
        ),
        (
            "MATCH (p:Page) RETURN p.url AS url; MATCH (n) DETACH DELETE n",
            "one statement",
        ),
        ("", "no query"),
    ],
)
def test_guard_refuses_writes_admin_and_escapes(query, reason):
    with pytest.raises(UnsafeCypher, match=reason):
        guard(query)


def test_extract_query_takes_the_fenced_block_and_drops_a_trailing_semicolon():
    assert extract_query(f"Here:\n```cypher\n{COUNT};\n```\nDone.") == COUNT
    assert extract_query(f"```\n{COUNT}\n```") == COUNT
    assert extract_query(f"  {COUNT};  ") == COUNT


def test_bounded_caps_rows_even_after_a_trailing_comment():
    wrapped = bounded(f"{COUNT} // last line", 7)
    assert wrapped.startswith("CALL () {\n")
    assert wrapped.endswith("\n}\nRETURN * LIMIT 7")


# --- the excerpt (G21) ---


def test_render_hides_vectors_and_bookkeeping_inside_whole_nodes():
    node = {
        "id": "c1",
        "text": "hello",
        "embedding": [0.1] * 1536,
        "build_id": "b",
        "embedding_model": "m",
    }
    text = render("Q", [{"c": node}], max_rows=10)
    assert "c: {id: c1, text: hello}" in text
    assert not any(hidden in text for hidden in HIDDEN)


def test_render_says_when_the_row_limit_was_hit_or_nothing_came_back():
    assert "there may be more" in render("Q", [{"n": 1}] * 3, max_rows=3)
    assert "there may be more" not in render("Q", [{"n": 1}] * 2, max_rows=3)
    assert "returned no rows" in render("Q", [], max_rows=3)


def test_render_stops_adding_rows_past_the_length_budget():
    rows = [{"text": "x" * 1400} for _ in range(40)]
    text = render("Q", rows, max_rows=50)
    assert len(text) < 21_000
    assert "more rows left out for length" in text


def test_the_prompt_describes_exactly_what_the_builder_writes():
    page = Page(
        url="https://x/a.md",
        title="A",
        markdown="# A\n\nSee [b](https://x/b) and `create_agent`.\n",
    )
    other = Page(url="https://x/b.md", title="B", markdown="# B\n\nText.\n")
    structure = build_structure([page, other], RecursiveChunker(Settings()))
    written: dict[str, set[str]] = {}
    for node in structure.nodes:
        written.setdefault(node.type.label, {node.type.key}).update(node.props)
    assert written == {label: set(props) for label, props in PROPERTIES.items()}
    assert "embedding" not in SYSTEM


# --- the strategy ---


def test_strategy_satisfies_the_port():
    _setup([], [])
    assert isinstance(factory.make_strategy(_settings()), RetrievalStrategy)


def test_rows_of_the_bounded_query_become_one_excerpt_without_a_page_url():
    graph, chat = _setup([COUNT], [[{"chunks": 4797}]])
    hits = factory.make_strategy(_settings()).retrieve("how many chunks?", 5)

    assert graph.queries == [bounded(COUNT, 3)]
    assert len(hits) == 1
    assert hits[0].chunk.source_url == ""
    assert COUNT in hits[0].chunk.text and "1. chunks: 4797" in hits[0].chunk.text
    assert chat.prompts[0] == (SYSTEM, "Question: how many chunks?")


def test_the_cypher_model_defaults_to_the_generation_model_and_can_be_set():
    _setup([], [])
    Text2CypherStrategy(_settings())
    assert _CHAT.model == "answer-model"
    Text2CypherStrategy(_settings(text2cypher_model="cypher-model"))
    assert _CHAT.model == "cypher-model"


def test_a_refused_query_goes_back_once_with_the_reason():
    bad = "MATCH (p:Page) SET p.title = 'x' RETURN p.url AS url"
    graph, chat = _setup([bad, COUNT], [[{"chunks": 1}]])
    hits = Text2CypherStrategy(_settings()).retrieve("q", 5)

    assert graph.queries == [
        bounded(COUNT, 3)
    ]  # the unsafe query never reached the store
    correction = chat.prompts[1][1]
    assert bad in correction and "SET is not allowed" in correction
    assert "chunks: 1" in hits[0].chunk.text


def test_a_server_error_goes_back_with_the_servers_message():
    error = GraphQueryError(
        "Neo.ClientError.Statement.SyntaxError", "Unknown function 'foo'"
    )
    _, chat = _setup(["MATCH (c) RETURN foo(c) AS x", COUNT], [error, [{"chunks": 2}]])
    Text2CypherStrategy(_settings()).retrieve("q", 5)
    assert "Unknown function 'foo'" in chat.prompts[1][1]


def test_a_model_that_never_writes_a_valid_query_yields_a_miss_not_an_error():
    error = GraphQueryError("Neo.ClientError.Statement.SyntaxError", "Invalid input")
    _, chat = _setup(["CREATE (n) RETURN n", "MATCH ("], [error])
    hits = Text2CypherStrategy(_settings()).retrieve("q", 5)

    assert len(chat.prompts) == 2
    assert (
        "No valid query" in hits[0].chunk.text and "Invalid input" in hits[0].chunk.text
    )


def test_a_write_the_server_refuses_means_the_guard_failed_and_raises():
    error = GraphQueryError(
        "Neo.ClientError.Statement.AccessMode",
        "Writing in read access mode not allowed",
    )
    _setup([COUNT], [error])
    with pytest.raises(UnsafeCypher, match="guard let through"):
        Text2CypherStrategy(_settings()).retrieve("q", 5)


def test_unbuilt_graph_raises_empty_index():
    _setup([], [], build=None)
    with pytest.raises(EmptyIndex):
        Text2CypherStrategy(_settings()).retrieve("q", 5)


def test_graph_from_another_snapshot_is_refused():
    _setup([], [])
    with pytest.raises(StaleGraph, match="'snap', not 'other'"):
        Text2CypherStrategy(_settings(snapshot="other")).retrieve("q", 5)


def test_the_embedding_model_does_not_matter_since_no_question_is_embedded():
    _setup([COUNT], [[{"chunks": 1}]])
    hits = Text2CypherStrategy(_settings(embedding_model="model-b")).retrieve("q", 5)
    assert len(hits) == 1


def test_a_query_that_matches_nothing_gets_one_correction():
    narrow = "MATCH (p:Page) WHERE p.title = 'LangGraph Quickstart' RETURN p.url AS url"
    _, chat = _setup([narrow, COUNT], [[], [{"chunks": 3}]])
    hits = Text2CypherStrategy(_settings()).retrieve("q", 5)

    assert narrow in chat.prompts[1][1] and "matched no rows" in chat.prompts[1][1]
    assert "chunks: 3" in hits[0].chunk.text


def test_a_second_empty_result_is_served_since_nothing_may_match():
    _setup([COUNT, COUNT], [[], []])
    hits = Text2CypherStrategy(_settings()).retrieve("q", 5)
    assert "returned no rows" in hits[0].chunk.text
    assert "No valid query" not in hits[0].chunk.text


def test_an_empty_result_beats_a_correction_that_fails():
    error = GraphQueryError("Neo.ClientError.Statement.SyntaxError", "Invalid input")
    _setup([COUNT, "MATCH ("], [[], error])
    hits = Text2CypherStrategy(_settings()).retrieve("q", 5)
    assert COUNT in hits[0].chunk.text and "returned no rows" in hits[0].chunk.text
