---
title: afk.py looks for the task folder in the main checkout, not the worktree
status: inbox
requester: Jayson De los Reyes
date: 2026-11-25
appetite:
review_by:
---

# afk.py looks for the task folder in the main checkout, not the worktree

**Raw request:** "Capture the three afk.py problems as backlog ideas" (Jayson De los Reyes, 2026-11-25, Claude Code session)

**Problem (AI draft, needs a human to confirm):** `main()` in `afk.py` checks `docs/tasks/<task>/` under `--root`, the main checkout. All later reads use the worktree, where `STATE.md` is the truth. A task committed only on `kairyn/<task>` fails with `FAIL: no task folder`. Each start needed a temporary copy of the folder in the main checkout.

**Evidence:** Task 2026-11-25-skill-names-clash: `afk.py run` and `afk.py approve` both printed `FAIL: no task folder docs/tasks/2026-11-25-skill-names-clash/` until the folder was copied into `main` by hand, 4 times.

# Log

2026-11-25T00:44:39Z [capture] Created after task 2026-11-25-skill-names-clash from a user request. Status inbox, waiting for triage.
