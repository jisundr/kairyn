---
title: /kairyn:build fails when the main checkout is on the task branch
status: triaged
requester: Jayson De los Reyes
date: 2026-11-25
appetite: small batch
review_by:
---

# /kairyn:build fails when the main checkout is on the task branch

**Raw request:** "Please add this as backlog" (Jayson De los Reyes, 2026-11-25, Claude Code session, about the failed first start of task 2026-11-25-first-mate-hub)

**Problem (AI draft, needs a human to confirm):** The learning from task skill-names-clash says: commit the task folder on `kairyn/<task>` before `/kairyn:build`. If the main checkout stays on that branch, `afk.py` `add_worktree()` runs `git worktree add <wt> kairyn/<task>`, and git refuses a branch that is checked out. afk.py ends with a Python traceback (exit 1), not a `BLOCKED:` line.

**Evidence:**
- Task 2026-11-25-first-mate-hub, 2026-11-25T01:37Z: `CalledProcessError ... worktree add ... returned non-zero exit status 128`.
- Fix by hand: `git checkout main`, then copy the task folder back as untracked files (`git checkout kairyn/<task> -- docs/tasks/<task>`, `git restore --staged`). The second start passed readiness.

**Notes:** Inference: readiness can check the branch first and print `BLOCKED: <branch> is checked out in <path>; switch that checkout to another branch`. Also fix the learning line in `.kairyn/learnings.md`.

# Log

- 2026-11-25T01:42:55Z [capture] Created from a user request in a Claude Code session. Status inbox, waiting for triage.
- 2026-11-25T04:18:32Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-25T04:18:32Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
