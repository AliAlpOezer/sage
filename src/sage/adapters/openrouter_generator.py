"""Generator adapter: grounded answering via OpenRouter chat completions.

The excerpts are numbered in the order received — the caller prints its
source list from the same order, so citations like [2] line up.
"""

import time
from collections.abc import Sequence

import httpx

from sage.config import Settings
from sage.factory import register_generator
from sage.models import ScoredChunk

_URL = "https://openrouter.ai/api/v1/chat/completions"

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


@register_generator("openrouter")
class OpenRouterGenerator:
    def __init__(self, settings: Settings):
        self.api_key = settings.openrouter_api_key
        self.model = settings.generation_model

    def generate(self, question: str, context: Sequence[ScoredChunk]) -> str:
        user = f"Documentation excerpts:\n\n{_render_excerpts(context)}\n\nQuestion: {question}"
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=120, headers=headers) as client:
            for attempt in (1, 2, 3):
                response = client.post(_URL, json=payload)
                if response.status_code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                response.raise_for_status()
                break
        return response.json()["choices"][0]["message"]["content"]
