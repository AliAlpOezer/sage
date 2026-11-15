"""Generator adapters: grounded answering over any OpenAI-compatible chat endpoint.

Two backends share one implementation because the wire format is identical; only
the endpoint, the auth and the failover story differ:

- `omniroute` (default) — the local OmniRoute gateway. No API key, no per-key
  quota, and its own upstream fallback, so there is nothing here to fail over
  between. Its failure mode is "the daemon is not running", which the error
  message names explicitly.
- `openrouter` — kept reachable rather than deleted, for the case where a
  specific named model matters. A 429 rotates to the next OPENROUTER_API_KEY_<n>
  inside the client's transport (see `sage.openrouter`), so the retry loop here
  only sees a 429 once every key has refused.

The excerpts are numbered in the order received — the caller prints its
source list from the same order, so citations like [2] line up.
"""

import time
from collections.abc import Sequence

import httpx

from sage import openrouter
from sage.config import OMNIROUTE_API_KEY, Settings
from sage.factory import register_generator
from sage.models import ScoredChunk

_TIMEOUT = 300

_SYSTEM = """\
You answer questions about the LangChain documentation.

Rules:
- Answer ONLY from the numbered documentation excerpts provided. Do not use
  outside knowledge, even if you are confident.
- Cite excerpts inline as [1], [2], ... after each claim they support.
- If the excerpts do not contain the answer, say exactly that and name what
  seems to be missing. Do not guess.
- Be concise; code examples from the excerpts may be quoted verbatim."""


def _render_excerpts(context: Sequence[ScoredChunk]) -> str:
    parts = []
    for i, scored in enumerate(context, start=1):
        c = scored.chunk
        parts.append(f"[{i}] {c.title} ({c.source_url})\n{c.text}")
    return "\n\n---\n\n".join(parts)


class _ChatGenerator:
    """Shared POST /chat/completions loop. Subclasses supply url/model/auth."""

    url: str
    model: str
    max_tokens: int

    def _client(self) -> httpx.Client:
        raise NotImplementedError

    def _raise_for_status(self, response: httpx.Response) -> None:
        response.raise_for_status()

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> str:
        user = f"Documentation excerpts:\n\n{_render_excerpts(context)}\n\nQuestion: {question}"
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "stream": False,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
        }
        with self._client() as client:
            for attempt in (1, 2, 3):
                response = client.post(self.url, json=payload)
                if response.status_code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                break
        self._raise_for_status(response)
        return self._content(response.json())

    def _content(self, body: dict) -> str:
        if "choices" not in body:
            # OpenRouter can answer 200 with an error body when the upstream fails
            # after the request was accepted (e.g. a provider timeout, code 504).
            error = body.get("error") or {}
            raise RuntimeError(
                f"{self.model} returned no completion: upstream error "
                f"{error.get('code')}: {error.get('message')}"
            )
        message = body["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        if not content:
            # Reasoning models put their scratchpad in `reasoning_content` and only
            # then start the answer; hitting the ceiling first yields an empty
            # `content`, which reads like a refusal but is really truncation.
            raise RuntimeError(
                f"{self.model} returned an empty completion "
                f"(finish_reason={body['choices'][0].get('finish_reason')!r}). "
                "Raise SAGE_GENERATION_MAX_TOKENS - reasoning models spend the "
                "ceiling on thinking before the answer begins."
            )
        return content


@register_generator("omniroute")
class OmniRouteGenerator(_ChatGenerator):
    def __init__(self, settings: Settings):
        self.url = f"{settings.omniroute_base_url.rstrip('/')}/chat/completions"
        self.model = settings.resolved_generation_model
        self.max_tokens = settings.generation_max_tokens

    def _client(self) -> httpx.Client:
        return httpx.Client(
            timeout=_TIMEOUT, headers={"Authorization": f"Bearer {OMNIROUTE_API_KEY}"}
        )

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> str:
        try:
            return super().generate(question, context)
        except httpx.ConnectError as e:
            # Distinguish "nothing is listening on :20128" from a model-side
            # failure - opposite problems with opposite fixes.
            raise RuntimeError(
                f"OmniRoute gateway is not reachable at {self.url}. Start it with: "
                "omniroute serve --daemon --no-open --no-tray"
            ) from e


@register_generator("openrouter")
class OpenRouterGenerator(_ChatGenerator):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.url = f"{openrouter.OPENROUTER_BASE_URL}/chat/completions"
        self.model = settings.resolved_generation_model
        self.max_tokens = settings.generation_max_tokens
        openrouter.key_ring(settings)  # fail at construction if no keys are configured

    def _client(self) -> httpx.Client:
        return openrouter.client(self.settings, timeout=_TIMEOUT)

    def _raise_for_status(self, response: httpx.Response) -> None:
        openrouter.raise_for_status(response)
