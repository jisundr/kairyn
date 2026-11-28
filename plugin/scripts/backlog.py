#!/usr/bin/env python3
"""The scripted half of the kairyn backlog stage: every idea file write.

    python3 backlog.py capture --slug <slug> --title <t> --effort <level> --impact <level> \\
        --request <the user's words> --problem <draft> [--requester <name>]

All take --root (default: the current directory). capture writes
docs/backlog/<UTC YYYYMMDDHHMMSS>-<slug>.md with status inbox, and creates the folder and its
README.md if missing. It never overwrites a file: it prints one FAIL: line and exits 1.

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKLOG = "docs/backlog"
LEVELS = ("low", "medium", "high")
README = """# Backlog

Triaged ideas.

| Idea | Effort | Impact | Notes |
|---|---|---|---|
"""


def slug_arg(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", value):
        raise argparse.ArgumentTypeError(f"{value!r} is not lower-case words joined by hyphens")
    return value


def git_user(root: Path) -> str:
    result = subprocess.run(["git", "-C", str(root), "config", "user.name"], capture_output=True, text=True)
    return result.stdout.strip()


def capture(root: Path, a: argparse.Namespace) -> int:
    requester = a.requester or git_user(root)
    if not requester:
        print("FAIL: no requester: set git config user.name or pass --requester")
        return 1
    now = datetime.now(timezone.utc)
    title = " ".join(a.title.split())
    folder = root / BACKLOG
    path = folder / f"{now:%Y%m%d%H%M%S}-{a.slug}.md"
    # json.dumps gives a quoted string that YAML reads, whatever the text holds.
    text = f"""---
title: {json.dumps(title, ensure_ascii=False)}
status: inbox
requester: {json.dumps(requester, ensure_ascii=False)}
date: {now:%Y-%m-%d}
effort: {a.effort}
impact: {a.impact}
review_by:
---

# {title}

**Raw request:** {a.request}

**Problem (AI draft):** {" ".join(a.problem.split())}

# Log

{now:%Y-%m-%dT%H:%M:%SZ} [capture] Captured for {requester}. Status inbox. Effort {a.effort}, impact {a.impact} proposed by the AI.
"""
    folder.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as f:
            f.write(text)
    except FileExistsError:
        print(f"FAIL: {path.relative_to(root).as_posix()} exists; nothing changed")
        return 1
    try:
        with (folder / "README.md").open("x", encoding="utf-8") as f:
            f.write(README)
    except FileExistsError:
        pass  # the user's index stays as it is
    print(path.relative_to(root).as_posix())
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--root", type=Path, default=Path("."))
    c.add_argument("--slug", type=slug_arg, required=True)
    for name in ("--title", "--request", "--problem"):
        c.add_argument(name, required=True)
    for name in ("--effort", "--impact"):
        c.add_argument(name, choices=LEVELS, required=True)
    c.add_argument("--requester")
    a = ap.parse_args(argv)
    return capture(a.root.resolve(), a)


if __name__ == "__main__":
    sys.exit(main())
