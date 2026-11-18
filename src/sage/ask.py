"""Query loop CLI: embed question -> top-k -> assemble context -> generate.

    uv run python -m sage.ask "How do I use create_agent?"
    uv run python -m sage.ask -k 8 "..."

The actual loop lives in `sage.service.answer` (shared with the HTTP API);
this module is just the command-line front end.
"""

import argparse
import sys

from sage.service import EmptyIndex, answer


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the ingested docs a question.")
    parser.add_argument("question")
    parser.add_argument("-k", type=int, default=None, help="chunks to retrieve (default: SAGE_TOP_K)")
    args = parser.parse_args()
    # Windows consoles and pipes default to cp1252, which cannot encode every
    # character a doc title or answer may contain.
    sys.stdout.reconfigure(encoding="utf-8")

    try:
        result = answer(args.question, args.k)
    except EmptyIndex as e:
        raise SystemExit(str(e))

    print(result.answer)
    print("\nSources:")
    for s in result.sources:
        where = f" - {s.url}" if s.url else ""
        print(f"  [{s.n}] {s.title}{where}  (score {s.score:.3f})")


if __name__ == "__main__":
    main()
