#!/usr/bin/env python3
"""The scripted half of the kairyn retro stage: size checks the model must not guess.

    python3 retro.py size                       # learnings.md <used>/<budget>
    python3 retro.py fits <home> --add "<text>" # FITS, OVER <n>, KAIRYN-OWNED or MISSING

All take --root (default: the current directory). Budgets come from .harness/budgets.yml,
then the built-in budgets for files kairyn installs, as in budgets.py.
fits answers whether a learning can move into <home>:
    KAIRYN-OWNED  an upgrade replaces the file, so the learning becomes a backlog idea
    MISSING       no such file
    OVER <n>      the home goes <n> tokens over its budget, so the learning becomes a backlog idea
    FITS          the home stays within its budget (or has none)

Standard library only: consumers run this with a plain python3 (3.9 on macOS).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from budgets import Budget, budget_for, estimate_tokens, load_config, with_fallbacks
from kairyn_files import owner_of

LEARNINGS = ".kairyn/learnings.md"


def repo_budgets(root: Path) -> list[Budget]:
    config = root / ".harness" / "budgets.yml"
    return with_fallbacks(load_config(config)[0] if config.is_file() else [])


def learnings_size(root: Path) -> tuple[int, int]:
    """(used, budget) in estimated tokens for .kairyn/learnings.md."""
    path = root / LEARNINGS
    used = estimate_tokens(path.read_text()) if path.is_file() else 0
    budget = budget_for(LEARNINGS, repo_budgets(root))
    return used, budget.max_tokens if budget else 0


def fits(root: Path, home: str, text: str) -> str:
    if owner_of(home) == "plugin":
        return "KAIRYN-OWNED"
    path = root / home
    if not path.is_file():
        return "MISSING"
    budget = budget_for(home, repo_budgets(root))
    if budget is None:
        return "FITS"
    used = estimate_tokens(path.read_text().rstrip("\n") + "\n" + text)
    return "FITS" if used <= budget.max_tokens else f"OVER {used - budget.max_tokens}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", type=Path, default=Path("."))
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("size", parents=[common])
    f = sub.add_parser("fits", parents=[common])
    f.add_argument("home")
    f.add_argument("--add", required=True)
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if a.cmd == "size":
        used, budget = learnings_size(root)
        print(f"learnings.md {used}/{budget}")
    else:
        print(fits(root, a.home, a.add))
    return 0


if __name__ == "__main__":
    sys.exit(main())
