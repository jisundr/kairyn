---
title: Rule on linting stage outputs by hand has no home
status: inbox
requester: Jayson De los Reyes
date: 2026-11-23
appetite:
review_by:
---

# Rule on linting stage outputs by hand has no home

**Raw request:** learning L11 from retro task `2026-11-23-retro`, quoted word for word:

> To lint a stage output by hand, import `evals/checks.py` with both `evals` and `tests` on `sys.path`: it imports `split_front_matter` from `tests/helpers.py`.

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `.harness/workflows/testing-and-evals.md`. Reason: OVER 38.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L11. Status inbox, waiting for triage.
