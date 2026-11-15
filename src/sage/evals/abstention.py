"""Did the answer decline? The one score for a question the corpus cannot answer.

RAGAS has no fair metric for these triples: it rates a correct "the docs don't cover
this" as an irrelevant answer, and there is no right context to retrieve, so context
precision and recall sit near the floor by construction. Unanswerable triples get this
single binary judgement instead and stay out of the four RAGAS means.
"""

import re
from typing import Any

_PROMPT = """\
You grade a documentation assistant. The documentation does NOT contain the answer to \
the question below, so the only correct behaviour is to decline: say the documentation \
does not cover it, without supplying an answer from elsewhere.

Question: {question}

Assistant's answer:
{answer}

Did the assistant decline? Reply with exactly one word.
DECLINED = it said the documentation does not contain the answer and gave no \
substantive answer to the question.
ANSWERED = it gave an answer to the question, with or without a caveat."""

_VERDICT_RE = re.compile(r"\b(DECLINED|ANSWERED)\b")


def parse_verdict(reply: str) -> float | None:
    """1.0 declined, 0.0 answered, None when the judge said neither."""
    verdicts = _VERDICT_RE.findall(reply.upper())
    # A reasoning judge may name both words while thinking; its verdict comes last.
    return float(verdicts[-1] == "DECLINED") if verdicts else None


def judge_abstention(chat: Any, question: str, answer: str) -> float | None:
    """Ask the judge chat model (a LangChain chat model) for the verdict."""
    try:
        reply = chat.invoke(_PROMPT.format(question=question, answer=answer)).content
    except Exception as e:  # noqa: BLE001 - a failed judge call is a missing score, retried later
        print(f"  abstention judge failed: {type(e).__name__}: {str(e)[:120]}")
        return None
    return parse_verdict(reply if isinstance(reply, str) else str(reply))
