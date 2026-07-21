# sage

RAG over the LangChain docs, hand-built as a learning project. Each pipeline stage
(chunk/embed/vector-store/generate) is a swappable Protocol port, picked via `.env`.

Stack: Python 3.12, FastAPI, Qdrant (embedded), OpenRouter, uv, pytest, ragas
Slack channel: #proj-sage
Repo: https://github.com/AliAlpOezer/sage.git

## Context protocol — follow this before doing anything else

1. Read `docs/context/INDEX.md`. It is a routing table; it tells you which single topic
   file matches the task you were given.
2. Load **at most two** files from `docs/context/`. One is the normal case.
3. Do **not** glob, list, or bulk-read `docs/context/**`. Do not read a topic file
   "for background" — if INDEX.md did not route you to it, you do not need it.
4. If INDEX.md does not clearly route the task, read `docs/context/STATUS.md` only and
   proceed. Ask in-thread rather than reading more context.

Everything in `docs/context/` is self-contained. A topic file will never require you to
open another one.

## Ground rules

- Never add AI co-authorship trailers (`Co-Authored-By: Claude`, `Generated with…`) to
  commits or PR bodies.
- Branch before committing; never commit straight to the default branch.
- When you finish, update `docs/context/STATUS.md` in the same PR if project state changed.
