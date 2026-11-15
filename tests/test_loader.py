import pytest

from sage.loader import _title_of, parse_index
from sage.sources import SOURCES, clean_neo4j, clean_qdrant, resolve, strip_frontmatter


def _sitemap(*locs: str) -> str:
    return "<urlset>" + "".join(f"<url><loc>{u}</loc></url>" for u in locs) + "</urlset>"


def test_parse_index_keeps_only_prefixed_pages_and_dedupes():
    xml = _sitemap(
        "https://docs.langchain.com/oss/python/langchain/overview",
        "https://docs.langchain.com/oss/javascript/langchain/overview",
        "https://docs.langchain.com/oss/python/langchain/overview",
    )
    assert parse_index(xml, SOURCES["langchain"]) == [
        "https://docs.langchain.com/oss/python/langchain/overview.md"
    ]


def test_page_url_follows_each_sites_markdown_rule():
    assert (
        SOURCES["qdrant"].page_url("https://qdrant.tech/documentation/concepts/collections/")
        == "https://qdrant.tech/documentation/concepts/collections/index.md"
    )
    neo4j = "https://neo4j.com/docs/cypher-manual/current/introduction/"
    assert SOURCES["neo4j"].page_url(neo4j) == neo4j


def test_parse_index_matches_any_of_a_sources_prefixes():
    xml = _sitemap(
        "https://langfuse.com/docs/observability/overview",
        "https://langfuse.com/blog/some-post",
        "https://langfuse.com/self-hosting",
    )
    assert parse_index(xml, SOURCES["langfuse"]) == [
        "https://langfuse.com/docs/observability/overview.md",
        "https://langfuse.com/self-hosting.md",
    ]


def test_strip_frontmatter_leaves_a_later_rule_alone():
    assert strip_frontmatter('---\ntitle: "x"\n---\n\n# H\n\n---\nafter\n') == "\n# H\n\n---\nafter\n"


def test_clean_neo4j_drops_nav_and_footer():
    raw = (
        "---\ntitle: Introduction\n---\n\n[Skip to content](#skip)\n\nCypher Manual\n\n"
        "# Introduction\n\nBody.\n\nLicense: [Creative Commons 4.0](https://x)\n\n[banner](https://y)\n"
    )
    assert clean_neo4j(raw) == "# Introduction\n\nBody.\n"


def test_clean_qdrant_drops_preamble_and_snippet_notes():
    raw = (
        "> Explore the catalog\n\n# Collections\n\nBody.\n"
        "> This snippet is also available in Bash. See the [full snippet](https://x).\n\nMore.\n"
    )
    assert clean_qdrant(raw) == "# Collections\n\nBody.\n\nMore.\n"


def test_title_falls_back_to_the_url_slug():
    assert _title_of("https://neo4j.com/docs/getting-started/graph-database/", "no heading") == "graph database"


def test_resolve_rejects_unknown_source():
    with pytest.raises(ValueError, match="unknown SAGE_SOURCES"):
        resolve(("langchain", "nope"))


def _crawl_neo4j(handler, cache_dir):
    import asyncio

    import httpx

    from sage.loader import load_source

    source = SOURCES["neo4j-graphrag"]
    fast = type(source)(name="t", pages=source.pages, md_suffix=None)  # no fetch_delay

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await load_source(client, 1, fast, cache_dir)

    return asyncio.run(run())


def test_cached_pages_are_not_fetched_again(tmp_path):
    import httpx

    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(200, text="# Page", headers={"content-type": "text/markdown"})

    first = _crawl_neo4j(handler, tmp_path)
    assert len(first) == len(calls) == 7
    assert len(_crawl_neo4j(handler, tmp_path)) == 7
    assert len(calls) == 7  # second crawl came from the cache


def test_crawl_stops_asking_once_the_site_refuses(tmp_path, monkeypatch):
    import asyncio

    import httpx

    async def no_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    calls = []

    def handler(request):
        calls.append(str(request.url))
        ok = len(calls) <= 2
        return httpx.Response(200 if ok else 403, text="# Page", headers={"content-type": "text/markdown"})

    pages = _crawl_neo4j(handler, tmp_path)
    assert len(pages) == 2
    assert len(calls) == 2 + 3  # third page used its three attempts, the other four none
