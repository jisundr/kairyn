# 28. learnings.md merges with a driver that keeps a retro's removals

Date: 2026-11-28

## Status
Accepted

## Context
Task 2026-11-28-union-merge-restores-learnings. This repo's `.gitattributes` merged `.kairyn/learnings.md` by `union` (cb1f43f). A union merge keeps lines that one side deleted. A branch from before a retro thus restored the removed lines on a rebase, with no conflict: the 97e81eb retro lost 8 lines this way. A plain merge keeps the removals, but parallel appends then conflict. init-ships-union-merge was dropped for the same reason.

## Decision
- `scripts/merge_learnings.py` is the merge driver for `.kairyn/learnings.md`. It keeps lines that either side adds and drops base lines that either side removes. It compares whole lines (D2).
- The result is the current side's lines, then the lines that only the other side adds (A1).
- `--install` writes the `git config` entry once per clone. The `CLAUDE.md` Commands block names it (D4).
- A pytest runs a retro case and a parallel-append case through real git in a temp repo (D3).
- Consumer repos do not get the driver. The inbox idea consumer-learnings-merge-driver records it (D5).

## Consequences
- A clone with no driver entry merges the file as text. A retro case then conflicts, and no line comes back silently.
- GitHub does not run custom merge drivers. The driver acts on local merges and rebases (A2).
- Two branches that add the same line give one line. A line that appears twice can lose a copy (K2).
- `CLAUDE.md` is at 700/700 tokens. The upper-case rule moved out; `change-a-stage.md` states it.
