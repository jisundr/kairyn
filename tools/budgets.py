#!/usr/bin/env python3
"""Size budgets for markdown files, so what an AI reads stays lean.

Budgets live in .harness/budgets.yml as estimated tokens (characters / 4).
The first matching pattern wins, so list specific patterns before general ones.
Every markdown file must match a pattern; a new file with no budget fails.

Usage:
    python tools/budgets.py     # print usage per file, exit 1 if any file is over or unbudgeted
"""
import fnmatch
import math
import sys
from pathlib import Path

import yaml

SKIP_DIRS = {".git", ".venv", ".pytest_cache", "__pycache__", "node_modules"}
SKIP_PREFIXES = ("evals/results/",)


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4)


def load_budgets(path: Path) -> list[tuple[str, int]]:
    entries = (yaml.safe_load(path.read_text()) or {}).get("budgets", [])
    budgets = []
    for entry in entries:
        pattern, limit = entry.get("pattern"), entry.get("max_tokens")
        if not isinstance(pattern, str) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"bad budget entry {entry!r}: need pattern (str) and max_tokens (positive int)")
        budgets.append((pattern, limit))
    return budgets


def budget_for(rel_path: str, budgets: list[tuple[str, int]]) -> int | None:
    for pattern, limit in budgets:
        if fnmatch.fnmatchcase(rel_path, pattern):
            return limit
    return None


def find_docs(root: Path) -> list[str]:
    docs = []
    for path in root.rglob("*.md"):
        rel = path.relative_to(root).as_posix()
        if SKIP_DIRS & set(path.relative_to(root).parts) or rel.startswith(SKIP_PREFIXES):
            continue
        docs.append(rel)
    return sorted(docs)


def check(root: Path, budgets: list[tuple[str, int]]) -> list[str]:
    problems = []
    for rel in find_docs(root):
        limit = budget_for(rel, budgets)
        if limit is None:
            problems.append(f"{rel}: no budget (add a pattern to .harness/budgets.yml)")
            continue
        used = estimate_tokens((root / rel).read_text())
        if used > limit:
            problems.append(f"{rel}: ~{used} tokens, budget {limit} (over by {used - limit})")
    return problems


def report(root: Path, budgets: list[tuple[str, int]]) -> list[str]:
    rows = []
    for rel in find_docs(root):
        limit = budget_for(rel, budgets)
        used = estimate_tokens((root / rel).read_text())
        pct = used / limit if limit else float("inf")
        rows.append((pct, f"{used}/{limit if limit else '-'}".ljust(10) + f"{rel}"))
    return [line for _, line in sorted(rows, key=lambda r: -r[0])]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    budgets = load_budgets(root / ".harness" / "budgets.yml")
    print("tokens (est.) / budget")
    print("\n".join(report(root, budgets)))
    problems = check(root, budgets)
    for problem in problems:
        print(f"FAIL: {problem}")
    if not problems:
        print("OK: all files within budget")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
