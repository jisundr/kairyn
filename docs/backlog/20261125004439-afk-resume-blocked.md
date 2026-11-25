---
title: afk.py does not resume a blocked task
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by:
---

# afk.py does not resume a blocked task

**Raw request:** "Capture the three afk.py problems as backlog ideas" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** `afk-run.md` and the `afk.py` docstring say: fix the cause, then run `/kairyn:build <task>` again, and it resumes at `stage:`. But `run()` stops at once when `status` is not `in-progress`: it prints `STOP: <task> is blocked at build`. The user must set `status: in-progress` by hand.

**Evidence:** Task 2026-11-25-skill-names-clash: after a readiness fix and after a review fix, the rerun printed `STOP: ... blocked at build`. Each time `STATE.md` was edited to `in-progress` and committed by hand (`3907200`, `75356a0`).

# Log

2026-11-25T00:44:39Z [capture] Created after task 2026-11-25-skill-names-clash from a user request. Status inbox, waiting for triage.
