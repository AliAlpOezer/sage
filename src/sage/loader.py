"""Corpus loader: docs.langchain.com sitemap -> Page objects.

The sitemap is the complete page index (the friendlier /llms.txt hard-truncates
at 100K chars and loses the entire /oss/ section). Each page is fetchable as
clean markdown by appending .md to its URL. No HTML parsing.
"""

import asyncio
import re

import httpx

from sage.config import Settings
from sage.models import Page

_LOC_RE = re.compile(r"<loc>([^<]+)</loc>")


def parse_index(sitemap_xml: str, url_prefix: str) -> list[str]:
    urls = _LOC_RE.findall(sitemap_xml)
    in_scope = [u.rstrip("/") + ".md" for u in urls if u.startswith(url_prefix)]
    return list(dict.fromkeys(in_scope))  # dedupe, keep order


def _title_of(url: str, markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return url.rsplit("/", 1)[-1].removesuffix(".md").replace("-", " ")


async def _fetch_page(client: httpx.AsyncClient, sem: asyncio.Semaphore, url: str) -> Page | None:
    async with sem:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"  skipping {url}: {exc}")
            return None
    text = response.text
    return Page(url=url, title=_title_of(url, text), markdown=text)


async def load_pages(settings: Settings) -> list[Page]:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        index = await client.get(settings.docs_index_url)
        index.raise_for_status()
        urls = parse_index(index.text, settings.docs_url_prefix)
        print(f"index lists {len(urls)} pages under {settings.docs_url_prefix}")
        sem = asyncio.Semaphore(settings.fetch_concurrency)
        pages = await asyncio.gather(*(_fetch_page(client, sem, u) for u in urls))
    return [p for p in pages if p is not None]
