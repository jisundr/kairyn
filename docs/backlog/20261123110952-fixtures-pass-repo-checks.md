---
title: Rule that eval fixtures pass the repo checks has no home
status: dropped
requester: Jayson De los Reyes
date: 2026-11-23
appetite:
review_by:
---

# Rule that eval fixtures pass the repo checks has no home

**Raw request:** learning L22 from retro task `2026-11-23-retro`, quoted word for word:

> An eval fixture must pass the repo's own checks. After adding a harness doc, run `harness_docs.py --write`, or the agent cannot find it.

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `.harness/workflows/testing-and-evals.md`. Reason: OVER 32.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L22. Status inbox, waiting for triage.
2026-11-23T11:22:03Z [triage] Merged into `20261123112203-split-testing-and-evals.md`. Status dropped. Decided by Jayson De los Reyes.
