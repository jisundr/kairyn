---
title: The requirements eval request makes plain_language flaky
status: inbox
requester: Jayson
date: 2026-11-23
appetite:
review_by:
---

# The requirements eval request makes plain_language flaky

**Raw request:** "separate task for plain_language, then commit and open the PR" (Jayson, 2026-11-23, Claude Code session)

**Problem (AI draft, needs a human to confirm):** The eval request in `evals/runner.py` says "prints what would change". The requirements stage copies "would" into `REQUIREMENTS.md`, and `checks.ste_problems` counts each one as a hedge. `plain_language` then misses its 80% gate on runs where the stage did nothing wrong. We would know it improved when the metric passes at 10 runs on two runs in a row.

**Evidence:**
- Run `20261123T014549Z`: `plain_language` 7/10. All three failures list "hedge: would", from the request's words.
- Run `20261122T204013Z`: 6/10. Other runs: 8/10 to 10/10.
- The design-stage task left the requirements stage unchanged for this metric.

**Notes:** Two fixes: reword the request ("prints the changes it plans to make") or let the hedge check skip words quoted from the request. Rewording is smaller. It changes the requirements eval input, so rerun that eval at 10 runs.

# Log

2026-11-23T02:28:01Z [capture] Created from a chat request by Claude. Status inbox, waiting for triage.
