"""Frozen page snapshots: one fixed set of pages that every eval arm is built from.

A live crawl drifts as the docs change, so two stores ingested months apart hold
different corpora and their scores cannot be compared (`docs/context/graph.md`, G9).
A snapshot pins the corpus: the vector collection and the graph are both built from
it, with no network involved.

The manifest (url + content hash per page) is committed under `evals/snapshots/`;
the page content stays local under `data/snapshots/<name>/`, like the page cache.
Loading verifies every page against its hash, so a snapshot cannot change silently.

    uv run python -m sage.snapshot freeze langchain-2026-11-16 --sources langchain
    SAGE_SNAPSHOT=langchain-2026-11-16 uv run python -m sage.ingest
"""

import argparse
import asyncio
import hashlib
import json
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import httpx

from sage.config import Settings
from sage.loader import crawl_source, page_from_raw
from sage.models import Page
from sage.sources import SOURCES, resolve

MANIFEST_DIR = Path("evals/snapshots")
CONTENT_DIR = Path("data/snapshots")


class SnapshotError(RuntimeError):
    """The snapshot is missing, incomplete, or no longer matches its manifest."""


@dataclass(frozen=True)
class SnapshotPage:
    url: str
    source: str
    sha256: str  # of the raw markdown as fetched, before the source's cleaning


@dataclass(frozen=True)
class Manifest:
    name: str
    id: str  # hash over every (url, sha256): two snapshots match iff their ids do
    created: str
    pages: tuple[SnapshotPage, ...]


def _content_file(name: str, url: str) -> Path:
    return CONTENT_DIR / name / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.md"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def snapshot_id(pages: tuple[SnapshotPage, ...]) -> str:
    lines = "\n".join(f"{p.url} {p.sha256}" for p in sorted(pages, key=lambda p: p.url))
    return _sha256(lines)[:12]


def read_manifest(name: str) -> Manifest:
    path = MANIFEST_DIR / f"{name}.json"
    if not path.exists():
        raise SnapshotError(f"no snapshot manifest at {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    pages = tuple(SnapshotPage(**p) for p in raw["pages"])
    return Manifest(name=raw["name"], id=raw["id"], created=raw["created"], pages=pages)


def load_snapshot(name: str) -> list[Page]:
    """The snapshot's pages, cleaned like a live crawl. Reads disk only."""
    pages: list[Page] = []
    for entry in read_manifest(name).pages:
        file = _content_file(name, entry.url)
        if not file.exists():
            raise SnapshotError(f"snapshot {name}: content missing for {entry.url} ({file})")
        raw = file.read_text(encoding="utf-8")
        if _sha256(raw) != entry.sha256:
            raise SnapshotError(f"snapshot {name}: {entry.url} no longer matches its manifest hash")
        page = page_from_raw(entry.url, raw, SOURCES[entry.source])
        if page is not None:
            pages.append(page)
    return pages


async def freeze(name: str, settings: Settings) -> Manifest:
    """Crawl `settings.sources` once and pin the result as snapshot `name`."""
    manifest_path = MANIFEST_DIR / f"{name}.json"
    if manifest_path.exists():
        raise SnapshotError(f"{manifest_path} exists; a snapshot is frozen, pick a new name")
    content_dir = CONTENT_DIR / name
    content_dir.mkdir(parents=True, exist_ok=True)

    entries: list[SnapshotPage] = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for source in resolve(settings.sources):
            urls, raws, left_for_later = await crawl_source(
                client, settings.fetch_concurrency, source, content_dir
            )
            if left_for_later:
                raise SnapshotError(
                    f"[{source.name}] throttled with {left_for_later} pages unfetched; the fetched "
                    f"pages are kept in {content_dir}, run the same command again later"
                )
            fetched = {url: raw for url, raw in zip(urls, raws, strict=True) if raw is not None}
            print(f"[{source.name}] {len(fetched)} of {len(urls)} listed pages in the snapshot")
            entries += [SnapshotPage(url=u, source=source.name, sha256=_sha256(r)) for u, r in fetched.items()]

    pages = tuple(entries)
    manifest = Manifest(name=name, id=snapshot_id(pages), created=datetime.now().astimezone().date().isoformat(), pages=pages)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    body = {
        "name": manifest.name,
        "id": manifest.id,
        "created": manifest.created,
        "pages": [vars(p) for p in pages],
    }
    manifest_path.write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8")
    print(f"froze {len(pages)} pages as {name} (id {manifest.id}) -> {manifest_path}")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_freeze = sub.add_parser("freeze")
    p_freeze.add_argument("name")
    p_freeze.add_argument("--sources", help="comma-separated; default SAGE_SOURCES")
    p_show = sub.add_parser("show")
    p_show.add_argument("name")
    args = ap.parse_args()

    if args.cmd == "freeze":
        settings = Settings.from_env()
        if args.sources:
            settings = replace(settings, sources=tuple(s.strip() for s in args.sources.split(",")))
        asyncio.run(freeze(args.name, settings))
    else:
        manifest = read_manifest(args.name)
        print(f"{manifest.name}: id {manifest.id}, {len(manifest.pages)} pages, created {manifest.created}")


if __name__ == "__main__":
    main()
