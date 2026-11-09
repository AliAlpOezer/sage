"""OpenRouter access with API-key rotation on 429.

Keys come from the environment as OPENROUTER_API_KEY_1, OPENROUTER_API_KEY_2, ...
(read by `config.read_openrouter_keys`). The process holds one *current* key. A 429
on it makes the next key current, and the last key wraps back to
OPENROUTER_API_KEY_1, so later requests start from the key that last worked
instead of re-hitting an exhausted one. A single request tries each key at most
once; when every key answers 429, the caller gets that 429, and
`raise_for_status` turns it into `OpenRouterKeysExhausted`. A 429 that the
model's *provider* raised (see `is_upstream_limit`) is returned at once without
rotating: it limits every caller, so no key can get past it.

A 402 (no credit for a paid model) rotates too, so paid calls such as
embeddings find the funded key. Each `pool` keeps its own pointer: embeddings
settle on the funded key while chat traffic still walks the free keys in order.

The rotation lives in an httpx transport so every OpenRouter caller shares one
pointer: the generator and embedder (plain httpx) and the RAGAS judge (the OpenAI
SDK inside langchain_openai, which accepts injected httpx clients).

Caveat from OpenRouter's limits page (checked 2026-11-09): "Making additional
accounts or API keys will not affect your rate limits, as we govern capacity
globally." The rotation warnings show whether that holds for a given key set:
if key 2 is refused the moment key 1 is, the limit is not per key.
"""

import logging
import threading
from collections.abc import Sequence
from typing import Any

import httpx

from sage.config import Settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# The OpenAI SDK refuses an empty api_key. The transport overwrites the
# Authorization header on every request, so this value is never sent.
_PLACEHOLDER_KEY = "set-by-rotating-transport"

log = logging.getLogger(__name__)

# 429: this key's rate limit is spent. 402: this key's account has no credit for a
# paid model. Either way another key may succeed, so both rotate.
_ROTATE_ON = frozenset({402, 429})


class OpenRouterKeysExhausted(RuntimeError):
    """Every configured OpenRouter key answered 429 to the same request."""


class OpenRouterUpstreamLimited(RuntimeError):
    """The model's provider answered 429; it limits all callers, whatever the key."""


class KeyRing:
    """The current-key pointer over ordered (env name, key) pairs."""

    def __init__(self, keys: Sequence[tuple[str, str]]):
        if not keys:
            raise RuntimeError(
                "No OpenRouter keys configured: set OPENROUTER_API_KEY_1 "
                "(and optionally _2, _3, ...) in .env."
            )
        self._keys = tuple(keys)
        self._current = 0
        self._lock = threading.Lock()

    def __len__(self) -> int:
        return len(self._keys)

    def current(self) -> tuple[int, str]:
        """(slot, key) of the key new requests should use."""
        with self._lock:
            return self._current, self._keys[self._current][1]

    def name(self, slot: int) -> str:
        return self._keys[slot][0]

    def rotate_past(self, slot: int, status: int = 429) -> None:
        """Key `slot` got a 429 or 402: make the next key current, wrapping last -> first.

        A no-op when another request already rotated past `slot`, so concurrent
        429s on one key advance the pointer once, not once per request.
        """
        with self._lock:
            if self._current != slot:
                return
            self._current = (slot + 1) % len(self._keys)
            log.warning(
                "OpenRouter %s on %s, switching to %s",
                status,
                self.name(slot),
                self.name(self._current),
            )


def is_upstream_limit(response: httpx.Response) -> bool:
    """True for a 429 raised by the model's provider rather than against our key.

    OpenRouter relays provider errors with `error.metadata.provider_name`, e.g.
    "google/gemma-4-31b-it:free is temporarily rate-limited upstream". That limit
    applies to every caller, so rotating keys only burns requests.
    """
    try:
        metadata = response.json()["error"].get("metadata") or {}
    except (ValueError, KeyError, TypeError, AttributeError):
        return False
    return "provider_name" in metadata


class RotatingKeyTransport(httpx.BaseTransport):
    """Sends with the ring's current key; on a key-level 429, rotates and resends."""

    def __init__(self, ring: KeyRing, inner: httpx.BaseTransport | None = None):
        self._ring = ring
        self._inner = inner or httpx.HTTPTransport()

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        request.read()  # buffer the body so it can be resent
        for attempt in range(len(self._ring)):
            slot, key = self._ring.current()
            request.headers["Authorization"] = f"Bearer {key}"
            response = self._inner.handle_request(request)
            if response.status_code not in _ROTATE_ON:
                return response
            response.read()
            if is_upstream_limit(response):
                return response
            self._ring.rotate_past(slot, response.status_code)
            if attempt < len(self._ring) - 1:
                response.close()
        return response

    def close(self) -> None:
        self._inner.close()


class AsyncRotatingKeyTransport(httpx.AsyncBaseTransport):
    """Async twin of `RotatingKeyTransport`, sharing the same ring."""

    def __init__(self, ring: KeyRing, inner: httpx.AsyncBaseTransport | None = None):
        self._ring = ring
        self._inner = inner or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        await request.aread()
        for attempt in range(len(self._ring)):
            slot, key = self._ring.current()
            request.headers["Authorization"] = f"Bearer {key}"
            response = await self._inner.handle_async_request(request)
            if response.status_code not in _ROTATE_ON:
                return response
            await response.aread()
            if is_upstream_limit(response):
                return response
            self._ring.rotate_past(slot, response.status_code)
            if attempt < len(self._ring) - 1:
                await response.aclose()
        return response

    async def aclose(self) -> None:
        await self._inner.aclose()


_rings: dict[tuple[str, tuple[tuple[str, str], ...]], KeyRing] = {}
_rings_lock = threading.Lock()


def key_ring(settings: Settings, pool: str = "chat") -> KeyRing:
    """The process-wide ring for these keys, so all callers rotate together."""
    keys = settings.openrouter_api_keys
    ring_id = (pool, keys)
    with _rings_lock:
        if ring_id not in _rings:
            _rings[ring_id] = KeyRing(keys)
        return _rings[ring_id]


def client(settings: Settings, pool: str = "chat", **kwargs: Any) -> httpx.Client:
    return httpx.Client(
        transport=RotatingKeyTransport(key_ring(settings, pool)), **kwargs
    )


def async_client(
    settings: Settings, pool: str = "chat", **kwargs: Any
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=AsyncRotatingKeyTransport(key_ring(settings, pool)), **kwargs
    )


def openai_kwargs(
    settings: Settings, timeout: float, pool: str = "chat"
) -> dict[str, Any]:
    """Constructor kwargs pointing a langchain_openai model at OpenRouter with rotation."""
    return {
        "api_key": _PLACEHOLDER_KEY,
        "base_url": OPENROUTER_BASE_URL,
        "http_client": client(settings, pool, timeout=timeout),
        "http_async_client": async_client(settings, pool, timeout=timeout),
    }


def raise_for_status(response: httpx.Response) -> None:
    """`response.raise_for_status()`, with a 429 reported by its cause.

    A key-level 429 reaching here means the transport already tried every key.
    OpenRouter's body says which limit hit (per-minute or per-day), so keep it.
    """
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429 and is_upstream_limit(e.response):
            raise OpenRouterUpstreamLimited(
                "The model's provider is rate-limiting it for everyone; another key "
                "will not help. Retry later or pick another model. "
                f"Response: {e.response.text[:300]}"
            ) from e
        if e.response.status_code == 402:
            raise OpenRouterKeysExhausted(
                "No OpenRouter key has credit for this request (402 on every key). "
                "Paid models need the funded key; use a ':free' model otherwise. "
                f"Last response: {e.response.text[:300]}"
            ) from e
        if e.response.status_code == 429:
            raise OpenRouterKeysExhausted(
                "Every OpenRouter key (OPENROUTER_API_KEY_1..N) returned 429. "
                f"Last response: {e.response.text[:300]}"
            ) from e
        raise
