# sage

RAG over the LangChain docs, hand-built as a learning project. Each pipeline stage
(chunk/embed/vector-store/generate) is a swappable Protocol port, picked via `.env`.

Stack: Python 3.12, FastAPI, Qdrant (embedded), OpenRouter, uv, pytest, ragas
Slack channel: #proj-sage
Repo: https://github.com/AliAlpOezer/sage.git

## Context protocol - follow this before doing anything else

1. Read `docs/context/INDEX.md`. It is a routing table; it tells you which single topic
   file matches the task you were given.
2. Load **at most two** files from `docs/context/`. One is the normal case.
3. Do **not** glob, list, or bulk-read `docs/context/**`. Do not read a topic file
   "for background" - if INDEX.md did not route you to it, you do not need it.
4. If INDEX.md does not clearly route the task, read `docs/context/STATUS.md` only and
   proceed. Ask in-thread rather than reading more context.

Everything in `docs/context/` is self-contained. A topic file will never require you to
open another one.

## Ground rules

- Never add AI co-authorship trailers (`Co-Authored-By: <agent>`, `Generated with…`) to
  commits or PR bodies.
- Branch before committing; never commit straight to the default branch.
- When you finish, update `docs/context/STATUS.md` in the same PR if project state changed.


## Shared knowledge

Keep this file as the canonical project contract for every harness. Native adapters
reference it. Preserve existing context/wiki paths, source evidence, and domain rules.
For documentation or memory work, follow `~/dotfiles/agents/docs/knowledge.md` when
available; outside this workstation, keep Markdown pages with YAML metadata, relative
links, a compact index, and a short update log. Read only task-relevant knowledge.
Personal skills live at `~/.agents/skills/`; project skills at `.agents/skills/` if present.

Private memory on Alp's workstation: `~/agent-memory/projects/C--Users-alial-dev-sage/memory/MEMORY.md`.
Read relevant entries only; preserve their dates and scope.
