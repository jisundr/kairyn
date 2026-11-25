---
title: afk.py crashes when the task folder is not committed
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by:
---

# afk.py crashes when the task folder is not committed

**Raw request:** "Capture the three afk.py problems as backlog ideas" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** `afk.py run` makes the worktree from `HEAD`. If the task folder is not committed, the worktree has no `STATE.md`, and `front()` fails with a `FileNotFoundError` traceback. The run prints no `BLOCKED:` line, and the skill reports nothing useful.

**Evidence:** Task 2026-11-25-skill-names-clash, first `/kairyn:build`: traceback at `afk.py` `state()`, path `.git/kairyn/worktrees/<task>/docs/tasks/<task>/STATE.md`. The fix was a hand commit of the task folder on `kairyn/<task>`.

# Log

2026-11-25T00:44:39Z [capture] Created after task 2026-11-25-skill-names-clash from a user request. Status inbox, waiting for triage.
2026-11-25T04:18:32Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-25T04:18:32Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
