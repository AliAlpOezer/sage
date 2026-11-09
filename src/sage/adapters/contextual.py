"""Contextual retrieval (Day 38): give each chunk the context it lost when it
was cut out of its page, *before* it is embedded.

The problem this attacks is the one the W6 plan names as "chunk can't stand
alone": a 1800-char slice of a LangChain docs page often says "pass it to the
constructor" without ever repeating which class, which page, or which section
it belongs to. The embedding of that slice therefore lands nowhere near a query
that names the class, and the retriever misses it.

The fix is a *prefix* prepended to the chunk text at ingest time, so the vector
encodes the situated chunk rather than the orphaned one::

    LangChain agents: creating and configuring ReAct-style agents with
    create_agent.
    > Agents > Runtime configuration

    <the original chunk text>

Two arms are registered, and they exist to be A/B'd against each other and
against `baseline` in the eval harness:

- ``structural`` — deterministic, zero LLM calls, zero cost. The prefix is the
  page title plus the chunk's markdown heading breadcrumb (``> H1 > H2``),
  recovered by locating the chunk back in its page. This is the free control
  arm: whatever it wins is what *structure alone* was worth.
- ``contextual`` — the same breadcrumb, plus a one-sentence LLM-written blurb
  describing what the whole page covers. This is the paid arm, and the delta
  between it and ``structural`` is the honest measure of what the LLM call buys.

Deviation from Anthropic's published method, stated plainly because it matters
when reading the numbers: they situate *every chunk individually* (one LLM call
per chunk, passing the whole document each time). This corpus is 178 pages /
4973 chunks, which is ~4973 calls against a free gateway — hours of wall clock
and a rate-limit wall. Here the LLM call is made **once per page** (178 calls)
and its blurb is shared by every chunk on that page; the per-chunk half of the
context comes from the heading breadcrumb, which is free and exact. So the
prefix is page-level LLM context + chunk-level deterministic context, not
chunk-level LLM context. If ``contextual`` beats ``structural`` by enough to
care about, the per-chunk version is the obvious next experiment.

Blurbs are cached on disk keyed by page content, so a re-ingest (or a resumed
one) does not re-pay for them.

Both arms change `chunk.text`, and `Chunk.make_id` hashes the text — so they
produce different ids from `baseline` and MUST be ingested into their own
collection. The harness variants set that; see `evals/harness.py`.
"""

import hashlib
import json
import re
import time
from dataclasses import replace
from pathlib import Path

import httpx

from sage.config import OMNIROUTE_API_KEY, Settings
from sage.factory import register_chunker
from sage.models import Chunk, Page
from sage.ports import Chunker

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.MULTILINE)

_BLURB_SYSTEM = """\
You write one-sentence retrieval context lines for documentation pages.

Given a documentation page, reply with a SINGLE sentence (max 30 words) that
states what the page covers, naming the concrete API names, classes or
functions a reader would search for.

Rules:
- Output the sentence only. No preamble, no quotes, no markdown, no bullet.
- Name specifics, not generalities: "configuring create_agent with a
  checkpointer for state persistence" beats "how to configure agents".
- Describe the page as a whole, not any one section."""


# --- heading breadcrumbs -----------------------------------------------------
def _heading_offsets(markdown: str) -> list[tuple[int, str]]:
    """(offset, breadcrumb) for every heading, in document order.

    The breadcrumb at a heading is the trail of enclosing headings including
    itself, e.g. `Agents > Runtime configuration`. A heading of level N closes
    every open heading of level >= N, which is what makes `##` after `###`
    pop back out to depth 2 rather than nesting deeper.
    """
    out: list[tuple[int, str]] = []
    stack: list[tuple[int, str]] = []  # (level, text)
    for m in _HEADING_RE.finditer(markdown):
        level, text = len(m.group(1)), m.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, text))
        out.append((m.start(), " > ".join(t for _, t in stack)))
    return out


def _anchor_offset(markdown: str, chunk_text: str, cursor: int) -> int:
    """Where `chunk_text` starts in `markdown`, searching forward from `cursor`.

    The chunker strips and re-joins paragraphs, so a chunk is not always a
    literal substring of the page. The first line almost always is, so that is
    what gets matched. Chunks arrive in document order, hence the monotonic
    cursor: it keeps a line that repeats across the page (`### Parameters`)
    matching the occurrence that belongs to *this* chunk rather than the first
    one on the page.
    """
    first_line = next((ln.strip() for ln in chunk_text.splitlines() if ln.strip()), "")
    if not first_line:
        return cursor
    for needle in (chunk_text[:120], first_line, first_line[:80]):
        if not needle:
            continue
        found = markdown.find(needle, cursor)
        if found == -1:  # fall back to anywhere on the page
            found = markdown.find(needle)
        if found != -1:
            return found
    return cursor


def _breadcrumb_at(headings: list[tuple[int, str]], offset: int) -> str:
    """The breadcrumb of the last heading at or before `offset` ("" if none)."""
    trail = ""
    for start, crumb in headings:
        if start > offset:
            break
        trail = crumb
    return trail


def _build_prefix(page_title: str, blurb: str, breadcrumb: str) -> str:
    lines = [blurb.strip() or page_title.strip()]
    if breadcrumb and breadcrumb != page_title:
        lines.append(f"> {page_title} > {breadcrumb}")
    else:
        lines.append(f"> {page_title}")
    return "\n".join(lines)


# --- the LLM blurb, cached by page content -----------------------------------
class PageBlurbs:
    """One-sentence page descriptions, memoized on disk by page content hash.

    Keyed by content, not URL: if a page changes, its blurb is recomputed; if
    the ingest is re-run unchanged, nothing is re-paid. The cache is flushed
    after every miss so a run killed halfway keeps everything it bought.
    """

    def __init__(self, settings: Settings):
        self.path = Path(settings.contextual_blurb_cache)
        self.url = f"{settings.omniroute_base_url.rstrip('/')}/chat/completions"
        self.model = settings.resolved_generation_model
        self.max_tokens = settings.contextual_blurb_max_tokens
        self.cache: dict[str, str] = {}
        if self.path.exists():
            self.cache = json.loads(self.path.read_text(encoding="utf-8"))

    @staticmethod
    def _key(page: Page) -> str:
        digest = hashlib.sha256(page.markdown.encode()).hexdigest()[:16]
        return f"{page.url}#{digest}"

    def for_page(self, page: Page) -> str:
        key = self._key(page)
        if key in self.cache:
            return self.cache[key]
        blurb = self._ask(page)
        self.cache[key] = blurb
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.cache, indent=1, ensure_ascii=False), encoding="utf-8")
        return blurb

    def _ask(self, page: Page) -> str:
        # The blurb describes the page as a whole; the head carries the title,
        # intro and top-level headings, which is what that takes. Sending 200K
        # chars of API reference would cost far more and say the same thing.
        body = page.markdown[:6000]
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "stream": False,
            "messages": [
                {"role": "system", "content": _BLURB_SYSTEM},
                {"role": "user", "content": f"Page title: {page.title}\n\n{body}"},
            ],
        }
        headers = {"Authorization": f"Bearer {OMNIROUTE_API_KEY}"}
        try:
            with httpx.Client(timeout=300, headers=headers) as client:
                for attempt in (1, 2, 3):
                    response = client.post(self.url, json=payload)
                    if response.status_code in (429, 500, 502, 503) and attempt < 3:
                        time.sleep(2**attempt)
                        continue
                    break
            response.raise_for_status()
            content = (response.json()["choices"][0]["message"].get("content") or "").strip()
        except (httpx.HTTPError, KeyError, ValueError) as e:
            # A missing blurb degrades this chunk to the `structural` arm rather
            # than failing a 178-page ingest on one bad page. Ingest prints it so
            # a run that quietly lost half its blurbs is visible, not silent.
            print(f"  blurb failed for {page.url}: {type(e).__name__}: {str(e)[:100]}")
            return ""
        # Models sometimes wrap the sentence in quotes or a bullet despite the
        # system prompt; strip that rather than embedding the punctuation.
        return content.strip().lstrip("-*• ").strip('"').strip().replace("\n", " ")


# --- the chunker ------------------------------------------------------------
class ContextualChunker:
    """Wraps a base chunker and prepends a situating prefix to every chunk.

    `blurbs=None` is the `structural` arm (breadcrumb only, no LLM).
    """

    def __init__(self, base: Chunker, blurbs: PageBlurbs | None):
        self.base = base
        self.blurbs = blurbs

    def chunk(self, page: Page) -> list[Chunk]:
        chunks = self.base.chunk(page)
        if not chunks:
            return []
        blurb = self.blurbs.for_page(page) if self.blurbs is not None else ""
        headings = _heading_offsets(page.markdown)

        out: list[Chunk] = []
        cursor = 0
        for c in chunks:
            offset = _anchor_offset(page.markdown, c.text, cursor)
            cursor = max(cursor, offset)
            prefix = _build_prefix(page.title, blurb, _breadcrumb_at(headings, offset))
            text = f"{prefix}\n\n{c.text}"
            # Re-hash: the id is a hash of the text, and the text just changed.
            out.append(replace(c, id=Chunk.make_id(page.url, text), text=text))
        return out


def _base_chunker(settings: Settings) -> Chunker:
    # Built through the registry so the base arm stays swappable, with the
    # `contextual`/`structural` names themselves excluded — otherwise a
    # misconfigured base would recurse into this factory forever.
    from sage.factory import make_chunker

    name = settings.contextual_base_chunker
    if name in ("contextual", "structural"):
        raise ValueError(
            f"SAGE_CONTEXTUAL_BASE_CHUNKER cannot be {name!r} — it would wrap itself."
        )
    return make_chunker(replace(settings, chunker=name))


@register_chunker("structural")
def make_structural_chunker(settings: Settings) -> ContextualChunker:
    return ContextualChunker(_base_chunker(settings), blurbs=None)


@register_chunker("contextual")
def make_contextual_chunker(settings: Settings) -> ContextualChunker:
    return ContextualChunker(_base_chunker(settings), blurbs=PageBlurbs(settings))
