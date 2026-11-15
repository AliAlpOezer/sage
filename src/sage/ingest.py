"""Ingestion pipeline: load -> chunk -> embed -> upsert.

Idempotent by construction: chunk ids are content hashes, so re-running
upserts the same points instead of duplicating them.

    uv run python -m sage.ingest
"""

import asyncio
from itertools import batched

from sage.config import Settings
from sage.factory import make_chunker, make_embedder, make_vector_store
from sage.loader import load_pages

# Chunks embedded and upserted per round. Bounds peak memory (a vector is ~50 KB as
# Python floats) and means an interrupted run keeps everything before the failure.
INGEST_BATCH = 512


async def run(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    chunker = make_chunker(settings)
    embedder = make_embedder(settings)
    store = make_vector_store(settings)

    pages = await load_pages(settings)
    print(f"fetched {len(pages)} pages")

    chunks = [chunk for page in pages for chunk in chunker.chunk(page)]
    print(f"chunked into {len(chunks)} chunks")

    done = 0
    for batch in batched(chunks, INGEST_BATCH):
        vectors = await embedder.embed([chunk.text for chunk in batch])
        store.ensure_collection(dimension=len(vectors[0]))
        store.upsert(batch, vectors)
        done += len(batch)
        print(f"  embedded + stored {done}/{len(chunks)}")
    print(f"store now holds {store.count()} vectors")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
