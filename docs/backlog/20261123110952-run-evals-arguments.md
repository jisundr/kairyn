---
title: Rule on /run-evals arguments has no home
status: inbox
requester: Jayson De los Reyes
date: 2026-11-23
appetite:
review_by:
---

# Rule on /run-evals arguments has no home

**Raw request:** learning L18 from retro task `2026-11-23-retro`, quoted word for word:

> `/run-evals` with no arguments runs every eval whose dependencies changed, at 10 runs. `--all-evals` with names runs only those names. For a cheap check, name the eval and add `--runs 2`.

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `.harness/workflows/testing-and-evals.md`. Reason: OVER 45.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L18. Status inbox, waiting for triage.
