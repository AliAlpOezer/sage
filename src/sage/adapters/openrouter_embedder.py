"""Embedder adapter: OpenRouter's OpenAI-compatible /embeddings endpoint.

Batches the input and runs batches concurrently under a semaphore — unbounded
gather over hundreds of requests would trip rate limits and exhaust sockets.
"""

import asyncio
from collections.abc import Sequence

import httpx

from sage.config import Settings
from sage.factory import register_embedder

_URL = "https://openrouter.ai/api/v1/embeddings"


@register_embedder("openrouter")
class OpenRouterEmbedder:
    def __init__(self, settings: Settings):
        self.api_keys = [k for k in (settings.openrouter_api_key, settings.openrouter_api_key_2) if k]
        self.model = settings.embedding_model
        self.batch_size = settings.embed_batch_size
        self.concurrency = settings.embed_concurrency

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not self.api_keys:
            raise RuntimeError("OPENROUTER_API_KEY missing — needed for embeddings.")
        batches = [texts[i : i + self.batch_size] for i in range(0, len(texts), self.batch_size)]
        sem = asyncio.Semaphore(self.concurrency)
        async with httpx.AsyncClient(timeout=60) as client:
            results = await asyncio.gather(
                *(self._embed_batch(client, sem, batch) for batch in batches)
            )
        return [vector for batch_vectors in results for vector in batch_vectors]

    async def _embed_batch(
        self, client: httpx.AsyncClient, sem: asyncio.Semaphore, batch: Sequence[str]
    ) -> list[list[float]]:
        payload = {"model": self.model, "input": list(batch)}
        async with sem:
            for key_index, key in enumerate(self.api_keys):
                is_last_key = key_index == len(self.api_keys) - 1
                headers = {"Authorization": f"Bearer {key}"}
                for attempt in (1, 2, 3):
                    response = await client.post(_URL, json=payload, headers=headers)
                    if response.status_code in (429, 500, 502, 503) and attempt < 3:
                        await asyncio.sleep(2**attempt)
                        continue
                    break
                # A 429 means this key's own rate limit is exhausted, not a
                # transient blip - move to the next key rather than burning
                # its retry budget too.
                if response.status_code == 429 and not is_last_key:
                    continue
                break
        response.raise_for_status()
        data = response.json()["data"]
        # The API echoes an index per item; sort by it rather than trusting order.
        return [item["embedding"] for item in sorted(data, key=lambda d: d["index"])]
