"""RetrievalStrategy adapter: `text2cypher`, an LLM writes one read query over the structural graph.

1. Write: the model sees the structural schema (labels, properties, relationships; no
   embeddings, no build bookkeeping), a few worked examples and the question, and
   replies with one Cypher query.
2. Guard (graph.md G12): string literals and comments are masked, then any write or
   admin clause, procedure call, query option or second statement is refused before
   anything is sent. The query runs wrapped as `CALL () { ... } RETURN * LIMIT n`, in
   the store's read session (the server refuses writes) with its timeout.
3. Correct (G22): a query the guard or the server refuses, or one that matches
   nothing, goes back to the model once, with the reason. A model that still fails
   yields an excerpt saying so, scored as a miss (a second empty result is served as
   the answer: nothing may really match). A write the guard let through raises,
   since that is a bug in the guard.
4. Context (G21): the query and its rows become one excerpt for the generator.
"""

import logging
import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from sage.config import Settings
from sage.factory import make_chat_model, make_graph_store, register_strategy
from sage.graph.current import check_build
from sage.graph.schema import (
    CHUNK,
    EMBEDDING,
    EMBEDDING_MODEL,
    HAS_CHUNK,
    LINKS_TO,
    MENTIONS,
    NEXT,
    PAGE,
    PAGE_HAS_SECTION,
    SECTION,
    SECTION_HAS_SECTION,
    SYMBOL,
)
from sage.models import Chunk, ScoredChunk
from sage.ports import GraphQueryError

log = logging.getLogger(__name__)

# Attempts per question: the first query plus one correction.
ATTEMPTS = 2
NO_ROWS = (
    "it ran but matched no rows. Check every name and word it matches against the "
    "schema notes, and loosen the match if the question expects results."
)
# A cell longer than this is cut (a chunk's text is up to ~1,800 characters).
CELL_CHARS = 1500
# Rows stop being added once the excerpt passes this; the generator's prompt stays bounded.
CONTEXT_CHARS = 20_000
# Build bookkeeping and vectors: never shown to either model.
HIDDEN = frozenset({EMBEDDING, EMBEDDING_MODEL, "build_id"})

# The properties the model is told about, per node type. A test pins these to
# what the structural builder writes, so the prompt cannot drift from the graph.
PROPERTIES: Mapping[str, tuple[str, ...]] = {
    PAGE.label: ("url", "title"),
    SECTION.label: ("id", "title", "level", "path", "position", "page_url"),
    CHUNK.label: ("id", "text", "source_url", "title", "position"),
    SYMBOL.label: ("name",),
}


def _node(node_type) -> str:
    return f"(:{node_type.label} {{{', '.join(PROPERTIES[node_type.label])}}})"


SCHEMA = f"""\
Nodes:
- {_node(PAGE)}:
  one documentation page. `url` is its full URL, ending in `.md`, e.g.
  https://docs.langchain.com/oss/python/langgraph/quickstart.md. The path segment
  after /python/ names the product: langchain, langgraph, deepagents, integrations,
  ... Titles are short and repeat across products (three pages are titled
  "Quickstart"), so match a product through `url`, not `title`.
- {_node(SECTION)}:
  one heading of a page. `path` joins the heading titles from the page's top down
  with " > "; `level` is the markdown heading level (1-6); `position` orders the
  sections of one page; `page_url` is the page's url. Every page also has one
  level-0 section with an empty title: the text before its first heading.
- {_node(CHUNK)}:
  a passage of a section's text, the unit search results are made of.
  `source_url` is its page's url, `title` its page's title; `position` orders the
  chunks of one page.
- {_node(SYMBOL)}:
  a code identifier the prose writes in backticks, e.g. `create_agent`,
  `ChatOpenAI`, `InMemorySaver`. Names are exact and case-sensitive.

Relationships:
- (:{PAGE.label})-[:{PAGE_HAS_SECTION.type}]->(:{SECTION.label}): a page's top-level headings.
- (:{SECTION.label})-[:{SECTION_HAS_SECTION.type}]->(:{SECTION.label}): a heading's subheadings.
- (:{SECTION.label})-[:{HAS_CHUNK.type}]->(:{CHUNK.label}): the passages directly under a heading.
- (:{CHUNK.label})-[:{NEXT.type}]->(:{CHUNK.label}): the passage that follows on the same page.
- (:{PAGE.label})-[:{LINKS_TO.type} {{count}}]->(:{PAGE.label}): the first page links to the second,
  `count` times.
- (:{CHUNK.label})-[:{MENTIONS.type}]->(:{SYMBOL.label}): the passage names the symbol."""

SYSTEM = f"""\
You translate questions about the LangChain documentation into one Cypher query over
a graph of that documentation. The graph's schema, complete:

{SCHEMA}

Rules:
- Write exactly one read-only query. Never CREATE, MERGE, SET, DELETE, REMOVE, DROP,
  FOREACH, LOAD CSV or USE; never CALL a procedure. CALL () {{ ... }} subqueries are fine.
- Return named properties with `AS`, never whole nodes or relationships.
- Match words from the question case-insensitively: toLower(x) CONTAINS 'word'.
  Symbol names are matched exactly.
- When the answer comes from passages, return their `text` and `source_url`, so the
  answer can be checked and cited.
- Reply with the query alone, in one ```cypher block.

Examples:

Question: How many pages mention create_agent?
```cypher
MATCH (:{SYMBOL.label} {{name: 'create_agent'}})<-[:{MENTIONS.type}]-(c:{CHUNK.label})
RETURN count(DISTINCT c.source_url) AS pages
```

Question: Which pages link to the page about streaming?
```cypher
MATCH (source:{PAGE.label})-[:{LINKS_TO.type}]->(target:{PAGE.label})
WHERE toLower(target.title) CONTAINS 'streaming'
RETURN target.title AS linked_page, source.title AS from_page, source.url AS from_url
```

Question: What are the subsections of the memory overview page?
```cypher
MATCH (p:{PAGE.label})-[:{PAGE_HAS_SECTION.type}]->(top:{SECTION.label})-[:{SECTION_HAS_SECTION.type}*0..]->(s:{SECTION.label})
WHERE toLower(p.title) CONTAINS 'memory'
RETURN p.url AS page, s.path AS section, s.level AS level ORDER BY page, s.position
```

Question: How do I add a checkpointer to an agent?
```cypher
MATCH (c:{CHUNK.label})
WHERE toLower(c.text) CONTAINS 'checkpointer' AND toLower(c.text) CONTAINS 'agent'
RETURN c.source_url AS url, c.text AS text LIMIT 8
```"""


class UnsafeCypher(ValueError):
    """A query that could write, administer, or escape the read-only wrapper."""


# Comments, string literals and backticked names: masked before the keyword scan, so
# `CONTAINS 'set up'` or a property called `delete` cannot trip it.
_OPAQUE = re.compile(
    r"""//[^\n]*|/\*.*?\*/|'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`[^`]*`""", re.DOTALL
)
_FORBIDDEN = re.compile(
    r"\b(CREATE|MERGE|SET|DELETE|DETACH|REMOVE|DROP|FOREACH|LOAD|USE|ALTER|RENAME|GRANT|DENY|REVOKE|"
    r"START|STOP|TERMINATE|SHOW|EXPLAIN|PROFILE|CYPHER)\b",
    re.IGNORECASE,
)
# CALL followed by anything but `{` or `(` names a procedure; subqueries are allowed.
_PROCEDURE = re.compile(r"\bCALL\s+(?![({])", re.IGNORECASE)
_TRANSACTIONS = re.compile(r"\bTRANSACTIONS\b", re.IGNORECASE)
_FENCE = re.compile(r"```[ \t]*(?:cypher)?[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_query(reply: str) -> str:
    """The query from a model reply: the first fenced block, else the whole reply."""
    match = _FENCE.search(reply)
    query = (match[1] if match else reply).strip()
    return query.removesuffix(";").rstrip()


def guard(query: str) -> None:
    """Raise `UnsafeCypher` unless `query` is a single statement with no write or admin clause."""
    if not query:
        raise UnsafeCypher("the reply holds no query")
    masked = _OPAQUE.sub(" ", query)
    if ";" in masked:
        raise UnsafeCypher("only one statement is allowed")
    if found := _FORBIDDEN.search(masked):
        raise UnsafeCypher(
            f"{found[1].upper()} is not allowed: the query must only read"
        )
    if _PROCEDURE.search(masked):
        raise UnsafeCypher(
            "procedure calls are not allowed; CALL () { ... } subqueries are"
        )
    if _TRANSACTIONS.search(masked):
        raise UnsafeCypher("CALL ... IN TRANSACTIONS is not allowed")


def bounded(query: str, max_rows: int) -> str:
    """`query` as a subquery whose rows are cut at `max_rows`, whatever LIMIT it states.

    The newlines keep a trailing `//` comment from swallowing the closing brace. The
    outer `RETURN *` keeps the rows in the inner query's order but lists columns by name.
    """
    return f"CALL () {{\n{query}\n}}\nRETURN * LIMIT {int(max_rows)}"


def _cell(value: Any) -> str:
    if isinstance(value, Mapping):
        value = {k: v for k, v in value.items() if k not in HIDDEN}
        return "{" + ", ".join(f"{k}: {_cell(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list | tuple):
        return "[" + ", ".join(_cell(v) for v in value) + "]"
    if isinstance(value, float):
        return f"{value:.4g}"
    text = str(value)
    return text if len(text) <= CELL_CHARS else text[:CELL_CHARS] + " [...]"


def render(query: str, rows: Sequence[Mapping[str, Any]], max_rows: int) -> str:
    """The excerpt the generator reads: the query, then one numbered line per row."""
    lines = ["Cypher query run against the documentation graph:", query, ""]
    if not rows:
        lines.append("The query returned no rows.")
        return "\n".join(lines)
    capped = " (the row limit: there may be more)" if len(rows) >= max_rows else ""
    lines.append(f"Result, {len(rows)} rows{capped}:")
    size = sum(len(line) + 1 for line in lines)
    for i, row in enumerate(rows, start=1):
        cells = (f"{k}: {_cell(v)}" for k, v in row.items() if k not in HIDDEN)
        line = f"{i}. " + "; ".join(cells)
        if size + len(line) > CONTEXT_CHARS:
            lines.append(f"({len(rows) - i + 1} more rows left out for length)")
            break
        lines.append(line)
        size += len(line) + 1
    return "\n".join(lines)


def _excerpt(text: str) -> ScoredChunk:
    # Not a page passage, so no page URL; "source page retrieved" does not apply (G21).
    chunk = Chunk(
        id=Chunk.make_id("text2cypher", text),
        text=text,
        source_url="",
        title="Documentation graph query",
        position=0,
    )
    return ScoredChunk(chunk=chunk, score=1.0)


@register_strategy("text2cypher")
class Text2CypherStrategy:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = make_graph_store(settings)
        self.model = make_chat_model(
            replace(settings, generation_model=settings.resolved_text2cypher_model)
        )

    def _prompt(self, question: str, failed: Sequence[tuple[str, str]]) -> str:
        parts = [f"Question: {question}"]
        for query, reason in failed:
            parts.append(f"Your query\n```cypher\n{query}\n```\nfailed: {reason}")
        if failed:
            parts.append("Write a corrected query.")
        return "\n\n".join(parts)

    def retrieve(self, question: str, k: int) -> list[ScoredChunk]:
        check_build(self.store, self.settings, embeds_questions=False)
        max_rows = self.settings.text2cypher_max_rows
        failed: list[tuple[str, str]] = []
        empty: str | None = None  # the last query that ran but matched nothing
        for _ in range(ATTEMPTS):
            query = extract_query(
                self.model.complete(SYSTEM, self._prompt(question, failed))
            )
            try:
                guard(query)
                rows = self.store.read(bounded(query, max_rows))
            except UnsafeCypher as exc:
                failed.append((query, f"refused: {exc}"))
                continue
            except GraphQueryError as exc:
                if exc.code.endswith("AccessMode"):
                    raise UnsafeCypher(
                        f"the server refused a write the guard let through: {query!r}"
                    ) from exc
                failed.append((query, f"the database refused it: {exc.message}"))
                continue
            if rows:
                return [_excerpt(render(query, rows, max_rows))]
            empty = query
            failed.append((query, NO_ROWS))

        if empty is not None:
            return [_excerpt(render(empty, [], max_rows))]
        query, reason = failed[-1]
        log.warning("text2cypher gave up on %r: %s", question, reason)
        return [
            _excerpt(
                f"No valid query over the documentation graph could be written for this question. "
                f"The last attempt was:\n{query}\nIt failed: {reason}"
            )
        ]
