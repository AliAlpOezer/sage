"""Wire RAGAS's judge LLM + embeddings to an OpenAI-compatible endpoint.

RAGAS needs two model handles:
- an LLM judge  — decomposes claims / runs NLI / scores relevance (faithfulness,
  answer relevancy, context precision, context recall all call it)
- an embeddings model — answer relevancy embeds generated questions vs. the original

The judge defaults to the local **OmniRoute** gateway: no key, no per-key quota, and
it pools several providers' free endpoints, which is what makes a full four-metric
RAGAS run finish at all. OpenRouter's free tier caps at ~8 req/min and was 429ing
whole runs.

Embeddings stay on OpenRouter: OmniRoute's `/v1/embeddings` route rejects the
placeholder key (its free pool is chat-only), and the paid text-embedding-3-small
call is tiny (~$2e-7). A free judge can be flaky on structured output either way,
which is exactly why the protocol audits 20% of verdicts by hand.
"""

from typing import Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)
from ragas.run_config import RunConfig

from sage import openrouter
from sage.config import OMNIROUTE_API_KEY, Settings

_JUDGE_TIMEOUT = 300

# Keyed judge providers, all OpenAI-compatible: (base_url, settings attr, env name).
# `omniroute` (keyless local gateway) and `openrouter` (rotating OPENROUTER_API_KEY_<n>,
# see `sage.openrouter`) are wired separately in `judge_endpoint`.
# groq/gemini have real free tiers with much higher rpm + low latency.
_KEYED_PROVIDERS: dict[str, tuple[str, str, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "groq_api_key", "GROQ_API_KEY"),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini_api_key",
        "GEMINI_API_KEY",
    ),
}
_JUDGE_PROVIDERS = ("omniroute", "openrouter", *_KEYED_PROVIDERS)


def _build_embeddings(settings: Settings) -> LangchainEmbeddingsWrapper:
    emb = OpenAIEmbeddings(
        model=settings.embedding_model,
        # OpenRouter model ids ("openai/text-embedding-3-small") aren't known to
        # tiktoken; skip the client-side context-length tokenization it would need.
        check_embedding_ctx_length=False,
        **openrouter.openai_kwargs(settings, timeout=60, pool="embeddings"),
    )
    return LangchainEmbeddingsWrapper(emb)


def _build_chat(settings: Settings, endpoint: dict[str, Any]) -> LangchainLLMWrapper:
    chat = ChatOpenAI(
        model=settings.resolved_judge_model,
        **endpoint,
        temperature=0.0,
        # Reasoning models spend this ceiling thinking before emitting the verdict;
        # too low and RAGAS parses an empty string and records NaN.
        max_tokens=settings.judge_max_tokens,
        timeout=_JUDGE_TIMEOUT,
        max_retries=3,
    )
    return LangchainLLMWrapper(chat)


def judge_endpoint(settings: Settings) -> dict[str, Any]:
    """ChatOpenAI connection kwargs (base_url, api_key, ...) for the judge provider."""
    provider = settings.judge_provider
    if provider == "omniroute":  # keyless local gateway
        return {"base_url": settings.omniroute_base_url, "api_key": OMNIROUTE_API_KEY}
    if provider == "openrouter":
        return openrouter.openai_kwargs(settings, timeout=_JUDGE_TIMEOUT)
    if provider not in _KEYED_PROVIDERS:
        raise RuntimeError(
            f"unknown SAGE_JUDGE_PROVIDER={provider!r}; expected one of {sorted(_JUDGE_PROVIDERS)}"
        )
    base_url, key_attr, env_name = _KEYED_PROVIDERS[provider]
    key = getattr(settings, key_attr)
    if not key:
        raise RuntimeError(f"{env_name} missing — needed for judge_provider={provider}.")
    return {"base_url": base_url, "api_key": key}


def build_judge(settings: Settings | None = None):
    """Return (llm, embeddings) RAGAS wrappers.

    Judge LLM is routed by settings.judge_provider (default: the local OmniRoute
    gateway). Embeddings (needed by answer_relevancy) always go through OpenRouter's
    paid text-embedding-3-small — it's tiny (~$2e-7/call), and neither Groq nor
    OmniRoute's free pool offers an embeddings endpoint.
    """
    s = settings or Settings.from_env()
    return _build_chat(s, judge_endpoint(s)), _build_embeddings(s)


def build_judges(settings: Settings | None = None) -> list[tuple[LangchainLLMWrapper, LangchainEmbeddingsWrapper]]:
    """Return one (llm, embeddings) pair per available judge key.

    Groq's TPD limit is scoped per-organization, so separate accounts (separate
    keys in SAGE_GROQ_API_KEYS / GROQ_API_KEYS below) each carry their own quota.
    Splitting the eval set across them multiplies the effective daily budget.
    Falls back to a single judge (build_judge) for every other provider, or when
    no extra Groq keys are configured.
    """
    s = settings or Settings.from_env()
    if s.judge_provider == "groq" and s.groq_api_keys:
        keys = [s.groq_api_key, *s.groq_api_keys] if s.groq_api_key else list(s.groq_api_keys)
        base_url, _, _ = _KEYED_PROVIDERS["groq"]
        emb = _build_embeddings(s)
        return [(_build_chat(s, {"base_url": base_url, "api_key": k}), emb) for k in keys]
    return [build_judge(s)]


def default_run_config(settings: Settings | None = None) -> RunConfig:
    """RunConfig tuned to the judge provider's rate limits.

    OpenRouter free = 8 req/min → must serialize (max_workers=1) or every job 429s.
    Groq/Gemini free tiers allow far more (~30 rpm) → modest concurrency is safe and fast.
    OmniRoute has no rate limit of its own — it spreads load over a pool — but its
    upstreams are reasoning models with a slow first token, so the ceiling is wall
    clock, not quota: modest concurrency and a long per-call timeout.
    Retries + backoff absorb the occasional token-per-minute 429.
    """
    s = settings or Settings.from_env()
    if s.judge_provider == "openrouter":
        return RunConfig(max_workers=1, timeout=180, max_retries=8, max_wait=90)
    if s.judge_provider == "omniroute":
        return RunConfig(max_workers=4, timeout=300, max_retries=6, max_wait=40)
    return RunConfig(max_workers=3, timeout=120, max_retries=6, max_wait=40)


def default_metrics():
    """The sprint's four RAGAS metrics.

    - Faithfulness             — is the answer supported by retrieved context? (generation)
    - ResponseRelevancy        — does the answer address the question?        (generation)
    - LLMContextPrecisionWithReference — is retrieved context relevant?       (retrieval)
    - LLMContextRecall         — was the needed context retrieved?            (retrieval)
    """
    return [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextPrecisionWithReference(),
        LLMContextRecall(),
    ]
