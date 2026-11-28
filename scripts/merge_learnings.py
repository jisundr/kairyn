#!/usr/bin/env python3
"""Git merge driver for .kairyn/learnings.md: keep lines either side adds, drop lines either side removes.

A union merge keeps lines one side deleted, so a branch from before a retro restored the
lines the retro removed. This driver honours those removals and still merges parallel appends.
Result: the current side's lines that the other side did not remove, then the lines only the
other side adds. Lines are compared whole.

Usage (inside the repo):
  python3 scripts/merge_learnings.py --install    # once per clone: writes the git config entry
  python3 scripts/merge_learnings.py %O %A %B     # git runs this; writes the result to %A

A clone with no entry merges the file as text, so a retro case conflicts instead of restoring lines.
Standard library only, Python 3.9: git runs it with the python3 on PATH.
"""
import subprocess
import sys
from pathlib import Path

NAME = "learnings"
DRIVER = "python3 scripts/merge_learnings.py %O %A %B"


def merge(base: str, ours: str, theirs: str) -> str:
    base_lines, our_lines, their_lines = (text.splitlines() for text in (base, ours, theirs))
    base_set, our_set, their_set = set(base_lines), set(our_lines), set(their_lines)
    removed = (base_set - our_set) | (base_set - their_set)
    kept = [line for line in our_lines if line not in removed]
    added = []
    for line in their_lines:
        if line not in base_set and line not in our_set and line not in added:
            added.append(line)
    lines = kept + added
    return "\n".join(lines) + "\n" if lines else ""


def install() -> int:
    for key, value in ((f"merge.{NAME}.name", "learnings.md: keep appends, honour removals"),
                       (f"merge.{NAME}.driver", DRIVER)):
        subprocess.run(["git", "config", key, value], check=True)
        print(f"git config {key} '{value}'")
    return 0


def main(argv: list) -> int:
    if argv == ["--install"]:
        return install()
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    base, ours, theirs = (Path(p) for p in argv)
    texts = [p.read_text(encoding="utf-8") for p in (base, ours, theirs)]
    ours.write_text(merge(*texts), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
