"""The doc sites sage can ingest, and how each one serves a page as markdown.

Every source is a sitemap (or several) filtered by URL prefix. They differ in two
ways only: how a page URL turns into a markdown response, and what boilerplate the
site wraps around the content. Pick sources with `SAGE_SOURCES=langchain,qdrant,...`.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
_H1_RE = re.compile(r"^# ", re.MULTILINE)
_NEO4J_FOOTER_RE = re.compile(r"^License: \[Creative Commons", re.MULTILINE)
_QDRANT_SNIPPET_NOTE_RE = re.compile(r"^> This snippet is also available in .*\n", re.MULTILINE)


def strip_frontmatter(markdown: str) -> str:
    return _FRONTMATTER_RE.sub("", markdown, count=1)


def from_first_h1(markdown: str) -> str:
    """Drop everything above the page's H1 (site chrome). No H1: keep it all."""
    match = _H1_RE.search(markdown)
    return markdown[match.start() :] if match else markdown


def clean_neo4j(markdown: str) -> str:
    # Neo4j's markdown is the rendered HTML page converted on the fly, so it carries
    # the nav above the H1 and the license + conference banner below the content.
    body = from_first_h1(strip_frontmatter(markdown))
    footer = _NEO4J_FOOTER_RE.search(body)
    return body[: footer.start()].rstrip() + "\n" if footer else body


def clean_qdrant(markdown: str) -> str:
    return _QDRANT_SNIPPET_NOTE_RE.sub("", from_first_h1(markdown))


_SPHINX_ANCHOR_RE = re.compile(r" ¶$", re.MULTILINE)


def clean_sphinx(markdown: str) -> str:
    # Sphinx pages put a search box and index links above the H1, and end every
    # heading with a pilcrow permalink.
    return _SPHINX_ANCHOR_RE.sub("", from_first_h1(markdown))


def _unchanged(markdown: str) -> str:
    return markdown


@dataclass(frozen=True)
class DocSource:
    name: str
    sitemaps: tuple[str, ...] = ()
    prefixes: tuple[str, ...] = ()  # which sitemap entries are in scope
    pages: tuple[str, ...] = ()  # explicit page URLs, for a site without a sitemap
    # Appended to the page URL to get markdown. None = the site has no markdown URL
    # and serves it by content negotiation (`Accept: text/markdown`) instead.
    md_suffix: str | None = ".md"
    clean: Callable[[str], str] = _unchanged
    # Cap on parallel fetches for a site that throttles; None = SAGE_FETCH_CONCURRENCY.
    max_concurrency: int | None = None
    # Seconds a fetch slot rests after each request; with max_concurrency this
    # bounds the request rate (max_concurrency / fetch_delay per second).
    fetch_delay: float = 0.0

    def page_url(self, loc: str) -> str:
        return loc if self.md_suffix is None else loc.rstrip("/") + self.md_suffix


_NEO4J_MANUALS = (
    "getting-started",
    "cypher-manual/current",
    "python-manual/current",
    "genai/plugin/current",
    "graph-data-science/current",
)
_NEO4J_GRAPHRAG = "https://neo4j.com/docs/neo4j-graphrag-python/current/"
# neo4j.com rate-limits by request count, not width: about 200 quick requests and it
# answers 403 for minutes, even 2 wide (2026-11-10). Two slots resting 1 s each keep
# a crawl under 2 requests per second.
_NEO4J_FETCH_DELAY = 1.0
_NEO4J_GRAPHRAG_PAGES = ("user_guide_rag", "user_guide_kg_builder", "user_guide_pipeline", "api", "types", "llm")

SOURCES: dict[str, DocSource] = {
    s.name: s
    for s in (
        # langchain keeps its markdown untouched: chunk ids hash the text, and the
        # eval collection was built from it as served.
        DocSource(
            name="langchain",
            sitemaps=("https://docs.langchain.com/sitemap.xml",),
            prefixes=("https://docs.langchain.com/oss/python/",),
        ),
        DocSource(
            name="langfuse",
            sitemaps=("https://langfuse.com/sitemap.xml",),
            prefixes=(
                "https://langfuse.com/docs",
                "https://langfuse.com/integrations",
                "https://langfuse.com/self-hosting",
            ),
            clean=strip_frontmatter,
        ),
        DocSource(
            name="qdrant",
            sitemaps=("https://qdrant.tech/sitemap.xml",),
            prefixes=("https://qdrant.tech/documentation/",),
            md_suffix="/index.md",
            clean=clean_qdrant,
        ),
        # Neo4j has no site-wide docs sitemap: each manual publishes its own.
        DocSource(
            name="neo4j",
            sitemaps=tuple(f"https://neo4j.com/docs/{m}/sitemap.xml" for m in _NEO4J_MANUALS),
            prefixes=tuple(f"https://neo4j.com/docs/{m}/" for m in _NEO4J_MANUALS),
            md_suffix=None,
            clean=clean_neo4j,
            max_concurrency=2,
            fetch_delay=_NEO4J_FETCH_DELAY,
        ),
        # The GraphRAG package docs are a Sphinx site on neo4j.com: no sitemap, seven pages.
        DocSource(
            name="neo4j-graphrag",
            pages=(_NEO4J_GRAPHRAG, *(f"{_NEO4J_GRAPHRAG}{p}.html" for p in _NEO4J_GRAPHRAG_PAGES)),
            md_suffix=None,
            clean=clean_sphinx,
            max_concurrency=2,
            fetch_delay=_NEO4J_FETCH_DELAY,
        ),
        DocSource(
            name="ragas",
            sitemaps=("https://docs.ragas.io/sitemap.xml",),
            prefixes=("https://docs.ragas.io/en/stable/",),
            md_suffix="/index.md",
        ),
    )
}


def resolve(names: tuple[str, ...]) -> list[DocSource]:
    unknown = [n for n in names if n not in SOURCES]
    if unknown:
        raise ValueError(f"unknown SAGE_SOURCES {unknown}; expected any of {sorted(SOURCES)}")
    return [SOURCES[n] for n in names]
