#!/usr/bin/env python3
"""Size budgets for markdown files, so what an AI reads stays lean.

Budgets live in .harness/budgets.yml as estimated tokens (characters / 4), each
with a load class saying when the file is read:
    always     loaded in every session (keep it tiny)
    on-demand  read only when the task matches its read_when
    runtime    shipped in the plugin, read when a command or stage runs
The first matching pattern wins, so list specific patterns before general ones.
Every markdown file must match a pattern; a new file with no budget fails.

Set `strict: false` at the top of budgets.yml to ignore files that match no pattern
(for projects whose other markdown files are not ours to budget).

Files that kairyn installs have fallback budgets (FALLBACK_BUDGETS), checked after the
repo's own patterns, so a repo with its own strict budgets.yml still passes after init.

Usage:
    python budgets.py [--root DIR]   # DIR defaults to the current directory; exit 1 on any problem
"""
from __future__ import annotations

import fnmatch
import math
import sys
from pathlib import Path
from typing import NamedTuple

from simple_yaml import parse_budgets

LOAD_CLASSES = ("always", "on-demand", "runtime")


class Budget(NamedTuple):
    pattern: str
    max_tokens: int
    load: str


SKIP_DIRS = {".git", ".venv", ".pytest_cache", "__pycache__", "node_modules"}
# .base/ holds upgrade merge bases; .claude/worktrees/ holds full Claude Code checkouts. Neither is docs.
SKIP_PREFIXES = ("evals/results/", ".kairyn/.base/", ".claude/worktrees/")

# Checked after the repo's patterns, so the repo's own limit wins.
FALLBACK_BUDGETS = [
    Budget(".kairyn/stages/*.md", 500, "runtime"),
    Budget(".kairyn/templates/*.md", 200, "runtime"),
    Budget(".kairyn/learnings.md", 2000, "runtime"),
    Budget("docs/tasks/*/*.md", 1500, "runtime"),
    Budget(".harness/README.md", 600, "on-demand"),
    Budget(".harness/workflows/running-stages.md", 800, "on-demand"),
    Budget(".harness/workflows/task-lifecycle.md", 800, "on-demand"),
    Budget(".harness/workflows/keeping-docs-lean.md", 800, "on-demand"),
    Budget(".harness/workflows/afk-run.md", 800, "on-demand"),
]


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def load_config(path: Path) -> tuple[list[Budget], bool]:
    """Returns (budgets, strict)."""
    options, entries = parse_budgets(path.read_text())
    budgets = []
    for entry in entries:
        pattern, limit, load = entry.get("pattern"), entry.get("max_tokens"), entry.get("load")
        if not isinstance(pattern, str) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"bad budget entry {entry!r}: need pattern (str) and max_tokens (positive int)")
        if load not in LOAD_CLASSES:
            raise ValueError(f"bad budget entry {entry!r}: load must be one of {LOAD_CLASSES}")
        budgets.append(Budget(pattern, limit, load))
    return budgets, options.get("strict", True) is not False


def with_fallbacks(budgets: list[Budget]) -> list[Budget]:
    return budgets + FALLBACK_BUDGETS


def load_budgets(path: Path) -> list[Budget]:
    return load_config(path)[0]


def budget_for(rel_path: str, budgets: list[Budget]) -> Budget | None:
    for budget in budgets:
        if fnmatch.fnmatchcase(rel_path, budget.pattern):
            return budget
    return None


def find_docs(root: Path) -> list[str]:
    docs = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if SKIP_DIRS & set(path.relative_to(root).parts) or rel.startswith(SKIP_PREFIXES):
            continue
        docs.append(rel)
    return sorted(docs)


def check(root: Path, budgets: list[Budget], strict: bool = True) -> list[str]:
    problems = []
    for rel in find_docs(root):
        budget = budget_for(rel, budgets)
        if budget is None:
            if strict:
                problems.append(f"{rel}: no budget (add a pattern to .harness/budgets.yml)")
            continue
        used = estimate_tokens((root / rel).read_text())
        if used > budget.max_tokens:
            problems.append(f"{rel}: ~{used} tokens, budget {budget.max_tokens} (over by {used - budget.max_tokens})")
    return problems


def report(root: Path, budgets: list[Budget], strict: bool = True) -> list[str]:
    rows = []
    for rel in find_docs(root):
        budget = budget_for(rel, budgets)
        if budget is None and not strict:
            continue
        used = estimate_tokens((root / rel).read_text())
        limit = budget.max_tokens if budget else None
        pct = used / limit if limit else float("inf")
        rows.append((pct, f"{used}/{limit or '-'}".ljust(11) + (budget.load if budget else "-").ljust(11) + rel))
    return [line for _, line in sorted(rows, key=lambda r: -r[0])]


def root_from_args(argv: list[str]) -> Path:
    return Path(argv[argv.index("--root") + 1]).resolve() if "--root" in argv else Path.cwd()


def main(argv: list[str]) -> int:
    root = root_from_args(argv)
    budgets, strict = load_config(root / ".harness" / "budgets.yml")
    budgets = with_fallbacks(budgets)
    print("tokens/budget  load       file")
    print("\n".join(report(root, budgets, strict)))
    problems = check(root, budgets, strict)
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("OK: all files within budget")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
