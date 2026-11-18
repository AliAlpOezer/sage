"""What a page's raw markdown says about structure: sections, links, symbols.

Pure functions over text. Fenced code is never structure: a `# comment` line in a
code block is not a heading, and a link or backticked name inside one is sample
code, not prose pointing somewhere.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlsplit

_FENCE_RE = re.compile(r"[ \t]*(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
_LINK_RE = re.compile(r"(?<!!)\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?[^)]*\)")
_CODE_SPAN_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_SYMBOL_RE = re.compile(r"[A-Za-z_]\w*(?:[.\-]\w+)*")
_API_REFERENCE = "https://reference.langchain.com/"
_MD_SUFFIXES = ("/index.md", ".md")
_MIN_SYMBOL_CHARS = 3
# Backticked in prose all the time, and naming nothing a reader could look up.
_NOT_SYMBOLS = frozenset(
    ["None", "True", "False", "true", "false", "null", "undefined", "NaN", "str", "string", "int", "integer", "float", "bool", "boolean", "number", "bytes", "dict", "list", "tuple", "set", "object", "any", "Any", "void"]
)


@dataclass(frozen=True)
class Section:
    level: int  # heading depth 1-6; 0 is the text above a page's first heading
    title: str
    path: tuple[str, ...]  # titles from the outermost enclosing heading down to this one
    text: str  # the heading line and its own body, up to the next heading of any level
    parent: int | None  # index of the enclosing section in the list; None = top level


def _lines(markdown: str) -> Iterator[tuple[int, str, bool]]:
    """(start offset, line, is it fenced code) for every line. Fence lines count as code."""
    offset = 0
    fence = ""  # the opening marker while inside a fenced block
    for line in markdown.splitlines(keepends=True):
        marker = _FENCE_RE.match(line)
        if fence:
            closes = marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence)
            yield offset, line, True
            if closes and not line[marker.end() :].strip():
                fence = ""
        elif marker:
            fence = marker[1]
            yield offset, line, True
        else:
            yield offset, line, False
        offset += len(line)


def prose(markdown: str) -> str:
    """The text with fenced code blocks removed."""
    return "".join(line for _, line, fenced in _lines(markdown) if not fenced)


def parse_sections(markdown: str) -> list[Section]:
    """Split a page at its headings into sections, in document order, with the tree.

    A heading of depth n is a child of the nearest earlier heading of lower depth.
    The sections' `text`, concatenated, is the page (minus blank lines above the
    first heading), so chunking section by section loses nothing.
    """
    headings = [
        (offset, len(match[1]), match[2])
        for offset, line, fenced in _lines(markdown)
        if not fenced and (match := _HEADING_RE.match(line.rstrip("\r\n")))
    ]
    sections: list[Section] = []
    first = headings[0][0] if headings else len(markdown)
    if markdown[:first].strip():
        sections.append(Section(level=0, title="", path=(), text=markdown[:first], parent=None))

    open_sections: list[int] = []  # indexes of the headings enclosing the current position
    for i, (start, level, title) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else len(markdown)
        while open_sections and sections[open_sections[-1]].level >= level:
            open_sections.pop()
        parent = open_sections[-1] if open_sections else None
        path = (*(sections[parent].path if parent is not None else ()), title)
        sections.append(Section(level=level, title=title, path=path, text=markdown[start:end], parent=parent))
        open_sections.append(len(sections) - 1)
    return sections


def link_targets(markdown: str) -> list[str]:
    """Targets of the inline links in the prose, images excluded, in document order."""
    return _LINK_RE.findall(prose(markdown))


def page_key(url: str) -> str:
    """A page URL as links write it: no fragment, query, trailing slash or markdown suffix."""
    bare = urlsplit(urldefrag(url)[0])._replace(query="").geturl().rstrip("/")
    for suffix in _MD_SUFFIXES:
        if bare.endswith(suffix):
            return bare.removesuffix(suffix)
    return bare


def resolve_link(page_url: str, target: str) -> str | None:
    """The `page_key` a link on `page_url` points at; None for a same-page anchor or non-http link."""
    if target.startswith("#"):
        return None
    absolute = urljoin(page_key(page_url), target)
    if urlsplit(absolute).scheme not in ("http", "https"):
        return None
    return page_key(absolute)


def symbols(text: str) -> set[str]:
    """Code names the prose mentions: backticked identifiers and API-reference link targets.

    `invoke()` and `invoke` are one symbol. Dotted and hyphenated names are kept
    whole (`stream.messages`, `langchain-core`).
    """
    found = {span.strip().removesuffix("()") for span in _CODE_SPAN_RE.findall(prose(text))}
    found |= {
        page_key(target).rsplit("/", 1)[-1]
        for target in link_targets(text)
        if target.startswith(_API_REFERENCE)
    }
    return {
        name
        for name in found
        if len(name) >= _MIN_SYMBOL_CHARS and name not in _NOT_SYMBOLS and _SYMBOL_RE.fullmatch(name)
    }
