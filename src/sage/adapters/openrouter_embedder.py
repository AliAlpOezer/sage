"""Embedder adapter: OpenRouter's OpenAI-compatible /embeddings endpoint.

Batches the input and runs batches concurrently under a semaphore — unbounded
gather over hundreds of requests would trip rate limits and exhaust sockets.
A 429 rotates to the next OPENROUTER_API_KEY_<n> inside the client's transport
(see `sage.openrouter`); the retry loop here only sees one once every key refused.
"""

import asyncio
from collections.abc import Sequence

import httpx

from sage import openrouter
from sage.config import Settings
from sage.factory import register_embedder

_URL = f"{openrouter.OPENROUTER_BASE_URL}/embeddings"


@register_embedder("openrouter")
class OpenRouterEmbedder:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.embedding_model
        self.batch_size = settings.embed_batch_size
        self.concurrency = settings.embed_concurrency
        openrouter.key_ring(settings, "embeddings")  # fail at construction if no keys are configured

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        batches = [texts[i : i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        sem = asyncio.Semaphore(self.concurrency)
        async with openrouter.async_client(self.settings, "embeddings", timeout=60) as client:
            results = await asyncio.gather(
                *(self._embed_batch(client, sem, batch) for batch in batches)
            )
        return [vector for batch_vectors in results for vector in batch_vectors]

    async def _embed_batch(
        self, client: httpx.AsyncClient, sem: asyncio.Semaphore, batch: Sequence[str]
    ) -> list[list[float]]:
        payload = {"model": self.model, "input": list(batch)}
        async with sem:
            for attempt in (1, 2, 3):
                response = await client.post(_URL, json=payload)
                if response.status_code in (429, 500, 502, 503) and attempt < 3:
                    await asyncio.sleep(2**attempt)
                    continue
                break
        openrouter.raise_for_status(response)
        data = response.json()["data"]
        # The API echoes an index per item; sort by it rather than trusting order.
        return [item["embedding"] for item in sorted(data, key=lambda d: d["index"])]
