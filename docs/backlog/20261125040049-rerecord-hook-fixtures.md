---
title: A script records the hook payload fixtures again
status: parked
requester: Jayson De los Reyes
date: 2026-11-25
effort: low
impact: low
review_by: 2027-02-23
---

# A script records the hook payload fixtures again

**Raw request:** Review finding F5 of task 2026-11-25-first-mate-hub (Jayson De los Reyes, 2026-11-25, Claude Code session).

**Problem (AI draft, needs a human to confirm):** `tests/fixtures/hooks/` holds PostToolUse, PostToolUseFailure and Stop payloads recorded once by hand from a `claude -p` run. `milestones.py` `return_code` depends on their shape. If Claude Code changes the shape, no test fails.

**Evidence:**
- The recording steps are only in the message of commit 0347fc6.
- A success has no exit field; a failure has `error: "Exit code N\n..."`.

**Notes:** Inference: a script in `scripts/` runs `claude -p` with dump hooks and rewrites the fixtures, run before a release. It costs a few cents per run.

# Log

- 2026-11-25T04:00:49Z [capture] Created from review finding F5 at close. Status inbox, waiting for triage.
- 2026-11-25T04:18:32Z [triage] Parked: nothing breaks until Claude Code changes the payload shape, and each run costs money. Decided by Jayson De los Reyes.
- 2026-11-26T03:01:29Z [triage] Effort low, impact low confirmed by Jayson De los Reyes.
