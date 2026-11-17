#!/usr/bin/env python3
"""Size budgets for markdown files, so what an AI reads stays lean.

Budgets live in .harness/budgets.yml as estimated tokens (characters / 4), each
with a load class saying when the file is read:
    always     loaded in every session (keep it tiny)
    on-demand  read only when the task matches its read_when
    runtime    shipped in the plugin, read when a command or stage runs
The first matching pattern wins, so list specific patterns before general ones.
Every markdown file must match a pattern; a new file with no budget fails.

Usage:
    python tools/budgets.py     # print usage per file, exit 1 if any file is over or unbudgeted
"""
import fnmatch
import math
import sys
from pathlib import Path
from typing import NamedTuple

import yaml

LOAD_CLASSES = ("always", "on-demand", "runtime")


class Budget(NamedTuple):
    pattern: str
    max_tokens: int
    load: str


SKIP_DIRS = {".git", ".venv", ".pytest_cache", "__pycache__", "node_modules"}
SKIP_PREFIXES = ("evals/results/",)


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def load_budgets(path: Path) -> list[Budget]:
    entries = (yaml.safe_load(path.read_text()) or {}).get("budgets", [])
    budgets = []
    for entry in entries:
        pattern, limit, load = entry.get("pattern"), entry.get("max_tokens"), entry.get("load")
        if not isinstance(pattern, str) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"bad budget entry {entry!r}: need pattern (str) and max_tokens (positive int)")
        if load not in LOAD_CLASSES:
            raise ValueError(f"bad budget entry {entry!r}: load must be one of {LOAD_CLASSES}")
        budgets.append(Budget(pattern, limit, load))
    return budgets


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


def check(root: Path, budgets: list[Budget]) -> list[str]:
    problems = []
    for rel in find_docs(root):
        budget = budget_for(rel, budgets)
        if budget is None:
            problems.append(f"{rel}: no budget (add a pattern to .harness/budgets.yml)")
            continue
        used = estimate_tokens((root / rel).read_text())
        if used > budget.max_tokens:
            problems.append(f"{rel}: ~{used} tokens, budget {budget.max_tokens} (over by {used - budget.max_tokens})")
    return problems


def report(root: Path, budgets: list[Budget]) -> list[str]:
    rows = []
    for rel in find_docs(root):
        budget = budget_for(rel, budgets)
        used = estimate_tokens((root / rel).read_text())
        limit = budget.max_tokens if budget else None
        pct = used / limit if limit else float("inf")
        rows.append((pct, f"{used}/{limit or '-'}".ljust(11) + (budget.load if budget else "-").ljust(11) + rel))
    return [line for _, line in sorted(rows, key=lambda r: -r[0])]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    budgets = load_budgets(root / ".harness" / "budgets.yml")
    print("tokens/budget  load       file")
    print("\n".join(report(root, budgets)))
    problems = check(root, budgets)
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("OK: all files within budget")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
