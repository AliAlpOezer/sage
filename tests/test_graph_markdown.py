from sage.graph.markdown import (
    link_targets,
    page_key,
    parse_sections,
    prose,
    resolve_link,
    symbols,
)

PAGE = """\
> intro note

# Agents

Lead paragraph.

## Tools

Tools text.

```python
# not a heading
x = 1
```

### Errors ###

Errors text.

## Memory

Memory text.
"""


def test_sections_follow_the_heading_tree():
    sections = parse_sections(PAGE)

    assert [(s.level, s.title) for s in sections] == [
        (0, ""),
        (1, "Agents"),
        (2, "Tools"),
        (3, "Errors"),
        (2, "Memory"),
    ]
    assert [s.parent for s in sections] == [None, None, 1, 2, 1]
    assert sections[3].path == ("Agents", "Tools", "Errors")


def test_sections_concatenate_back_to_the_page():
    assert "".join(s.text for s in parse_sections(PAGE)) == PAGE


def test_a_heading_inside_a_code_fence_is_not_a_section():
    tools = parse_sections(PAGE)[2]

    assert "# not a heading" in tools.text
    assert tools.text.rstrip().endswith("```")


def test_a_longer_fence_is_not_closed_by_a_shorter_one():
    markdown = "# A\n\n````md\n```python\n# inner\n```\n# still code\n````\n\n# B\n"

    assert [s.title for s in parse_sections(markdown)] == ["A", "B"]


def test_an_indented_fence_still_hides_headings():
    markdown = "# A\n\n1. step\n\n   ```bash\n# comment\n   ```\n\n# B\n"

    assert [s.title for s in parse_sections(markdown)] == ["A", "B"]


def test_a_sibling_after_a_deeper_heading_returns_to_the_right_parent():
    sections = parse_sections("# A\n### deep\n## B\n# C\n")

    assert [s.parent for s in sections] == [None, 0, 0, None]


def test_page_without_headings_is_one_untitled_section():
    sections = parse_sections("just text\n")

    assert [(s.level, s.text) for s in sections] == [(0, "just text\n")]


def test_blank_page_has_no_sections():
    assert parse_sections("\n\n") == []


def test_prose_drops_fenced_code():
    assert prose("a\n```\ncode\n```\nb\n") == "a\nb\n"


def test_link_targets_skip_images_and_code():
    markdown = (
        "See [agents](https://x/agents#tools) and [`create_agent`](https://ref/create_agent \"t\").\n"
        "![diagram](https://x/img.svg)\n"
        "```md\n[sample](https://x/sample)\n```\n"
    )

    assert link_targets(markdown) == ["https://x/agents#tools", "https://ref/create_agent"]


def test_page_key_strips_what_links_do_not_write():
    assert page_key("https://x/docs/agents.md") == "https://x/docs/agents"
    assert page_key("https://x/docs/agents/index.md") == "https://x/docs/agents"
    assert page_key("https://x/docs/agents/?a=1#tools") == "https://x/docs/agents"


def test_resolve_link_handles_absolute_relative_and_anchors():
    page = "https://x/docs/agents.md"

    assert resolve_link(page, "https://x/docs/tools#section") == "https://x/docs/tools"
    assert resolve_link(page, "/docs/memory/") == "https://x/docs/memory"
    assert resolve_link(page, "models") == "https://x/docs/models"
    assert resolve_link(page, "#tools") is None
    assert resolve_link(page, "mailto:a@b.c") is None


def test_symbols_are_backticked_names_and_api_reference_targets():
    text = (
        "Call `create_agent` or `agent.invoke()`; install `langchain-core`.\n"
        "Returns `None`, a `str`, or `x`. Run `pip install -U langgraph`.\n"
        "See [interrupt](https://reference.langchain.com/python/langgraph/types/interrupt).\n"
        "```python\n`fenced_name`\n```\n"
    )

    assert symbols(text) == {"create_agent", "agent.invoke", "langchain-core", "interrupt"}
