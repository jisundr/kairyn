#!/usr/bin/env python3
"""Keep .harness docs readable without opening them.

Every doc starts with front matter:
    ---
    title: <name>
    summary: <one line, at most 160 characters>
    read_when: <the task that makes this doc relevant, e.g. "editing a stage">
    load: <always | on-demand | runtime>   # when it is read; the index lists on-demand docs
    ---
An agent reads only those lines to decide whether the doc matters. The index
tables in CLAUDE.md and .harness/README.md are generated from them.

Usage:
    python tools/harness_docs.py --check   # exit 1 if a header is bad or an index is stale
    python tools/harness_docs.py --write   # regenerate the index tables
"""
import re
import sys
from pathlib import Path

import yaml

from budgets import LOAD_CLASSES

KEYS = ("title", "summary", "read_when", "load")
MAX_SUMMARY = 160
START, END = "<!-- harness-docs:start -->", "<!-- harness-docs:end -->"


def read_meta(path: Path) -> dict | None:
    text = path.read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def doc_problems(path: Path, meta: dict | None) -> list[str]:
    if meta is None:
        return [f"{path.name}: missing front matter (title, summary, read_when, load)"]
    problems = []
    for key in KEYS:
        value = meta.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{path.name}: front matter needs a non-empty '{key}'")
        elif "\n" in value.strip():
            problems.append(f"{path.name}: '{key}' must be a single line")
    load = meta.get("load")
    if isinstance(load, str) and load.strip() and load.strip() not in LOAD_CLASSES:
        problems.append(f"{path.name}: load must be one of {LOAD_CLASSES}")
    summary = meta.get("summary")
    if isinstance(summary, str) and len(summary.strip()) > MAX_SUMMARY:
        problems.append(f"{path.name}: summary is over {MAX_SUMMARY} characters")
    return problems


def collect(root: Path) -> list[tuple[Path, dict | None]]:
    """The harness README first, then every workflow in name order."""
    paths = [p for p in [root / ".harness" / "README.md"] if p.exists()]
    paths += sorted((root / ".harness" / "workflows").glob("*.md"))
    return [(p, read_meta(p)) for p in paths]


def _valid(entries):
    """Docs with a good header that an agent should open on demand."""
    return [(p, m) for p, m in entries if m and not doc_problems(p, m) and m["load"] == "on-demand"]


def render_claude_table(entries, root: Path) -> str:
    rows = ["| When you are... | Read |", "|---|---|"]
    for path, meta in _valid(entries):
        rows.append(f"| {meta['read_when'].strip()} | `{path.relative_to(root).as_posix()}` |")
    return "\n".join(rows)


def render_readme_table(entries, root: Path) -> str:
    base = root / ".harness"
    rows = ["| Workflow | Use it when |", "|---|---|"]
    for path, meta in _valid(entries):
        if path.parent == base:
            continue  # the README does not index itself
        rows.append(f"| [{meta['title'].strip()}]({path.relative_to(base).as_posix()}) | {meta['read_when'].strip()} |")
    return "\n".join(rows)


def replace_block(text: str, new: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise ValueError(f"missing {START} ... {END} markers")
    return pattern.sub(lambda _: f"{START}\n{new}\n{END}", text, count=1)


def _targets(root: Path, entries):
    return {
        root / "CLAUDE.md": render_claude_table(entries, root),
        root / ".harness" / "README.md": render_readme_table(entries, root),
    }


def check(root: Path) -> list[str]:
    entries = collect(root)
    problems = [p for path, meta in entries for p in doc_problems(path, meta)]
    for target, table in _targets(root, entries).items():
        try:
            current = target.read_text()
            if replace_block(current, table) != current:
                problems.append(f"{target.relative_to(root)}: index is out of date")
        except (OSError, ValueError) as e:
            problems.append(f"{target.relative_to(root)}: {e}")
    return problems


def sync(root: Path) -> None:
    for target, table in _targets(root, collect(root)).items():
        target.write_text(replace_block(target.read_text(), table))


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    if "--write" in argv:
        sync(root)
        print("indexes updated")
    problems = check(root)
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("OK: harness docs verified")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
