"""Wire RAGAS's judge LLM + embeddings to OpenRouter.

RAGAS needs two model handles:
- an LLM judge  — decomposes claims / runs NLI / scores relevance (faithfulness,
  answer relevancy, context precision, context recall all call it)
- an embeddings model — answer relevancy embeds generated questions vs. the original

Both point at OpenRouter's OpenAI-compatible endpoints, reusing the one key. The
judge model is free by default (see config.judge_model) because the account balance
is negative; a free judge can be flaky on structured output, which is exactly why the
protocol audits 20% of verdicts by hand.
"""

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.run_config import RunConfig
from ragas.metrics import (
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
    ResponseRelevancy,
)

from sage.config import Settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Judge LLM providers, all OpenAI-compatible. OpenRouter's free tier caps at 8 req/min
# (too slow for RAGAS); groq/gemini have real free tiers with much higher rpm + low latency.
_JUDGE_PROVIDERS = {
    "openrouter": (OPENROUTER_BASE_URL, "openrouter_api_key", "OPENROUTER_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "groq_api_key", "GROQ_API_KEY"),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini_api_key",
        "GEMINI_API_KEY",
    ),
}


def build_judge(settings: Settings | None = None):
    """Return (llm, embeddings) RAGAS wrappers.

    Judge LLM is routed by settings.judge_provider. Embeddings (needed by
    answer_relevancy) always go through OpenRouter's paid text-embedding-3-small —
    it's tiny (~$2e-7/call) and Groq offers no embeddings endpoint.
    """
    s = settings or Settings.from_env()
    if s.judge_provider not in _JUDGE_PROVIDERS:
        raise RuntimeError(
            f"unknown SAGE_JUDGE_PROVIDER={s.judge_provider!r}; "
            f"expected one of {sorted(_JUDGE_PROVIDERS)}"
        )
    base_url, key_attr, env_name = _JUDGE_PROVIDERS[s.judge_provider]
    key = getattr(s, key_attr)
    if not key:
        raise RuntimeError(f"{env_name} missing — needed for judge_provider={s.judge_provider}.")
    if not s.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing — needed for judge embeddings.")

    chat = ChatOpenAI(
        model=s.judge_model,
        api_key=key,
        base_url=base_url,
        temperature=0.0,
        timeout=120,
        max_retries=3,
    )
    emb = OpenAIEmbeddings(
        model=s.embedding_model,
        api_key=s.openrouter_api_key,
        base_url=OPENROUTER_BASE_URL,
        # OpenRouter model ids ("openai/text-embedding-3-small") aren't known to
        # tiktoken; skip the client-side context-length tokenization it would need.
        check_embedding_ctx_length=False,
    )
    return LangchainLLMWrapper(chat), LangchainEmbeddingsWrapper(emb)


def default_run_config(settings: Settings | None = None) -> RunConfig:
    """RunConfig tuned to the judge provider's rate limits.

    OpenRouter free = 8 req/min → must serialize (max_workers=1) or every job 429s.
    Groq/Gemini free tiers allow far more (~30 rpm) → modest concurrency is safe and fast.
    Retries + backoff absorb the occasional token-per-minute 429.
    """
    s = settings or Settings.from_env()
    if s.judge_provider == "openrouter":
        return RunConfig(max_workers=1, timeout=180, max_retries=8, max_wait=90)
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
