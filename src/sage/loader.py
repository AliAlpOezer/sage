"""Corpus loader: doc-site sitemaps -> Page objects.

A sitemap is the complete page index (the friendlier /llms.txt files truncate or
list only top-level sections). Each page is fetched as clean markdown, by URL
suffix or content negotiation depending on the site (see `sage.sources`). No HTML
parsing.

Fetched pages are kept in a disk cache (`SAGE_PAGE_CACHE`), so a crawl that a site
throttles part-way keeps what it got and the next run fetches only the rest. Delete
the cache directory to pick up changed docs.
"""

import asyncio
import hashlib
import re
from pathlib import Path

import httpx

from sage.config import Settings
from sage.models import Page
from sage.sources import DocSource, resolve

_LOC_RE = re.compile(r"<loc>([^<]+)</loc>")
_MARKDOWN = {"Accept": "text/markdown"}
# Statuses a doc site answers when it is throttling us, not when the page is gone.
_THROTTLED = {403, 429, 502, 503}
_FETCH_ATTEMPTS = 3


def parse_index(sitemap_xml: str, source: DocSource) -> list[str]:
    locs = _LOC_RE.findall(sitemap_xml)
    in_scope = [source.page_url(u) for u in locs if u.startswith(source.prefixes)]
    return list(dict.fromkeys(in_scope))  # dedupe, keep order


def _title_of(url: str, markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return slug.removesuffix(".md").replace("-", " ")


async def _sitemap_urls(client: httpx.AsyncClient, sitemap: str, source: DocSource) -> list[str]:
    response = await client.get(sitemap)
    response.raise_for_status()
    if "<sitemapindex" not in response.text:
        return parse_index(response.text, source)
    children = _LOC_RE.findall(response.text)
    nested = await asyncio.gather(*(_sitemap_urls(client, c, source) for c in children))
    return list(dict.fromkeys(u for urls in nested for u in urls))


class _Crawl:
    """One source's fetch state: its rate limit, and whether the site shut us out."""

    def __init__(self, client: httpx.AsyncClient, source: DocSource, concurrency: int):
        self.client = client
        self.source = source
        self.sem = asyncio.Semaphore(min(concurrency, source.max_concurrency or concurrency))
        self.throttled = False
        self.left_for_later = 0

    async def download(self, url: str) -> str | None:
        """The page's raw markdown, or None if it could not be fetched this run."""
        for attempt in range(1, _FETCH_ATTEMPTS + 1):
            async with self.sem:
                if self.throttled:
                    # The site is refusing us: every further request only extends the
                    # block. Leave the rest for the next run; the cache keeps this one's.
                    self.left_for_later += 1
                    return None
                try:
                    response = await self.client.get(url, headers=_MARKDOWN)
                except httpx.HTTPError as exc:
                    print(f"  skipping {url}: {type(exc).__name__}")
                    return None
                await asyncio.sleep(self.source.fetch_delay)
            if response.status_code not in _THROTTLED:
                break
            if attempt == _FETCH_ATTEMPTS:
                self.throttled = True
                self.left_for_later += 1
                return None
            await asyncio.sleep(5 * 2**attempt)  # outside the semaphore: no slot held
        if response.status_code != 200:
            print(f"  skipping {url}: HTTP {response.status_code}")
            return None
        if "markdown" not in response.headers.get("content-type", ""):
            # A site that ignores the markdown request answers 200 with its HTML page.
            print(f"  skipping {url}: not markdown ({response.headers.get('content-type')})")
            return None
        return response.text


def _cache_file(cache_dir: Path | None, url: str) -> Path | None:
    return cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.md" if cache_dir else None


async def _load_page(crawl: _Crawl, url: str, cache_dir: Path | None) -> Page | None:
    cached = _cache_file(cache_dir, url)
    if cached and cached.exists():
        raw = cached.read_text(encoding="utf-8")
    else:
        raw = await crawl.download(url)
        if raw is None:
            return None
        if cached:
            cached.write_text(raw, encoding="utf-8")
    text = crawl.source.clean(raw)
    if not text.strip():
        return None
    return Page(url=url, title=_title_of(url, text), markdown=text)


async def load_source(
    client: httpx.AsyncClient, concurrency: int, source: DocSource, cache_dir: Path | None = None
) -> list[Page]:
    per_sitemap = await asyncio.gather(*(_sitemap_urls(client, s, source) for s in source.sitemaps))
    urls = list(dict.fromkeys([*(u for urls in per_sitemap for u in urls), *source.pages]))
    crawl = _Crawl(client, source, concurrency)
    loaded = await asyncio.gather(*(_load_page(crawl, u, cache_dir) for u in urls))
    pages = [p for p in loaded if p is not None]
    print(f"[{source.name}] {len(pages)} of {len(urls)} listed pages loaded")
    if crawl.left_for_later:
        print(
            f"[{source.name}] the site is throttling: {crawl.left_for_later} pages left for a "
            f"later run (wait a while, then run the same command again)"
        )
    return pages


async def load_pages(settings: Settings) -> list[Page]:
    cache_dir = Path(settings.page_cache) if settings.page_cache else None
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        pages: list[Page] = []
        for source in resolve(settings.sources):
            pages += await load_source(client, settings.fetch_concurrency, source, cache_dir)
    return pages
