import asyncio

import httpx
import pytest

from sage.config import read_openrouter_keys
from sage.openrouter import (
    AsyncRotatingKeyTransport,
    KeyRing,
    OpenRouterKeysExhausted,
    OpenRouterUpstreamLimited,
    RotatingKeyTransport,
    raise_for_status,
)

# The body OpenRouter relays when the model's provider, not our key, is limited.
UPSTREAM_429 = {
    "error": {
        "code": 429,
        "message": "Provider returned error",
        "metadata": {
            "raw": "rate-limited upstream",
            "provider_name": "Google AI Studio",
        },
    }
}

URL = "https://openrouter.ai/api/v1/chat/completions"


def _ring(n: int) -> KeyRing:
    return KeyRing([(f"OPENROUTER_API_KEY_{i}", f"key-{i}") for i in range(1, n + 1)])


def _fake_openrouter(limited: set[str], seen: list[str]) -> httpx.MockTransport:
    """Answers 429 for keys in `limited`, 200 otherwise; records the key of every call."""

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.headers["Authorization"].removeprefix("Bearer ")
        seen.append(key)
        return httpx.Response(429 if key in limited else 200, json={"key": key})

    return httpx.MockTransport(handler)


def _client(ring: KeyRing, limited: set[str], seen: list[str]) -> httpx.Client:
    return httpx.Client(
        transport=RotatingKeyTransport(ring, _fake_openrouter(limited, seen))
    )


def test_keys_are_read_in_numeric_order_and_blanks_skipped():
    env = {
        "OPENROUTER_API_KEY_10": "k10",
        "OPENROUTER_API_KEY_2": "k2",
        "OPENROUTER_API_KEY_1": " k1 ",
        "OPENROUTER_API_KEY_3": "  ",
        "OPENROUTER_API_KEY": "unnumbered",
        "OTHER": "x",
    }
    assert read_openrouter_keys(env) == (
        ("OPENROUTER_API_KEY_1", "k1"),
        ("OPENROUTER_API_KEY_2", "k2"),
        ("OPENROUTER_API_KEY_10", "k10"),
    )


def test_429_moves_to_next_key_and_later_requests_start_there():
    ring, seen = _ring(8), []
    with _client(ring, {"key-1"}, seen) as client:
        assert client.post(URL, json={}).json() == {"key": "key-2"}
        assert client.post(URL, json={}).json() == {"key": "key-2"}
    assert seen == ["key-1", "key-2", "key-2"]


def test_key_8_wraps_back_to_key_1():
    ring, seen = _ring(8), []
    limited = {f"key-{i}" for i in range(2, 9)}
    with _client(ring, limited, seen) as client:
        ring.rotate_past(0)  # start the request on key 2
        assert client.post(URL, json={}).json() == {"key": "key-1"}
    assert seen == [f"key-{i}" for i in range(2, 9)] + ["key-1"]


def test_every_key_429_tries_each_once_then_raises_exhausted():
    ring, seen = _ring(3), []
    with _client(ring, {"key-1", "key-2", "key-3"}, seen) as client:
        response = client.post(URL, json={})
    assert response.status_code == 429
    assert seen == ["key-1", "key-2", "key-3"]
    with pytest.raises(OpenRouterKeysExhausted):
        raise_for_status(response)
    # A full cycle of 429s wraps the pointer, so the next request starts at key 1.
    assert ring.current() == (0, "key-1")


def test_non_429_errors_are_not_rotated_or_relabelled():
    ring = _ring(2)
    transport = RotatingKeyTransport(
        ring, httpx.MockTransport(lambda r: httpx.Response(402))
    )
    with httpx.Client(transport=transport) as client:
        response = client.post(URL, json={})
    assert ring.current() == (0, "key-1")
    with pytest.raises(httpx.HTTPStatusError) as err:
        raise_for_status(response)
    assert not isinstance(err.value, OpenRouterKeysExhausted)


def test_upstream_provider_429_is_not_rotated():
    ring, seen = _ring(8), []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["Authorization"])
        return httpx.Response(429, json=UPSTREAM_429)

    transport = RotatingKeyTransport(ring, httpx.MockTransport(handler))
    with httpx.Client(transport=transport) as client:
        response = client.post(URL, json={})
    assert len(seen) == 1  # one try: another key cannot get past the provider
    assert ring.current() == (0, "key-1")
    with pytest.raises(OpenRouterUpstreamLimited):
        raise_for_status(response)


def test_concurrent_429s_on_one_key_advance_the_pointer_once():
    ring = _ring(8)
    ring.rotate_past(0)
    ring.rotate_past(0)  # a second request that also saw key 1 refuse
    assert ring.current() == (1, "key-2")


def test_async_transport_rotates_too():
    ring, seen = _ring(2), []
    transport = AsyncRotatingKeyTransport(ring, _fake_openrouter({"key-1"}, seen))

    async def call() -> dict:
        async with httpx.AsyncClient(transport=transport) as client:
            return (await client.post(URL, json={"input": ["x"]})).json()

    assert asyncio.run(call()) == {"key": "key-2"}
    assert seen == ["key-1", "key-2"]


def test_no_keys_is_a_clear_error():
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY_1"):
        KeyRing([])
