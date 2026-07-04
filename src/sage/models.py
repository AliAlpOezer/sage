"""Core data shapes shared by every component."""

import hashlib
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source_url: str
    title: str
    position: int

    @staticmethod
    def make_id(source_url: str, text: str) -> str:
        """Content-hash id: same content -> same id -> idempotent upserts."""
        digest = hashlib.sha256(f"{source_url}\n{text}".encode()).hexdigest()
        # Qdrant only accepts UUIDs or unsigned ints as point ids, so the
        # hash is formatted as a (deterministic) UUID.
        return str(uuid.UUID(hex=digest[:32]))


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    score: float
