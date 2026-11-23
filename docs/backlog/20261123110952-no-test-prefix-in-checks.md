---
title: No test stops check functions named test_
status: inbox
requester: Jayson De los Reyes
date: 2026-11-23
appetite:
review_by:
---

# No test stops check functions named test_

**Raw request:** learning L13 from retro task `2026-11-23-retro`, quoted word for word:

> pytest collects any imported function whose name starts with `test_`. Name check functions in `evals/checks.py` without that prefix (`design_test_plan_problems`).

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: a test. Reason: The home is a test: no function in `evals/checks.py` starts with `test_`.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L13. Status inbox, waiting for triage.
