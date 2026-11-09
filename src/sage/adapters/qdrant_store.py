"""VectorStore adapter: Qdrant in embedded local mode (no server, file-backed)."""

import atexit
from collections.abc import Sequence

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from sage.config import Settings
from sage.factory import register_vector_store
from sage.models import Chunk, ScoredChunk


@register_vector_store("qdrant")
class QdrantStore:
    def __init__(self, settings: Settings):
        self.client = QdrantClient(path=settings.qdrant_path)
        # Close before interpreter teardown: otherwise QdrantClient.__del__ runs after
        # sys.meta_path is gone and prints an ImportError traceback on every exit.
        atexit.register(self.client.close)
        self.collection = settings.collection

    def ensure_collection(self, dimension: int) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def upsert(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        points = [
            PointStruct(
                id=chunk.id,
                vector=list(vector),
                payload={
                    "text": chunk.text,
                    "source_url": chunk.source_url,
                    "title": chunk.title,
                    "position": chunk.position,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: Sequence[float], k: int) -> list[ScoredChunk]:
        hits = self.client.query_points(
            collection_name=self.collection, query=list(vector), limit=k
        ).points
        return [
            ScoredChunk(
                chunk=Chunk(
                    id=str(hit.id),
                    text=hit.payload["text"],
                    source_url=hit.payload["source_url"],
                    title=hit.payload["title"],
                    position=hit.payload["position"],
                ),
                score=hit.score,
            )
            for hit in hits
        ]

    def count(self) -> int:
        return self.client.count(collection_name=self.collection).count
