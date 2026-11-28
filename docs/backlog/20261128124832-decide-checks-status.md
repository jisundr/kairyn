---
title: "backlog.py decide does not check the current status"
status: triaged
requester: "Jayson De los Reyes"
date: 2026-11-28
effort: low
impact: medium
review_by:
---

# backlog.py decide does not check the current status

**Raw request:** Reviewer note on PR #82, kept as a follow-up idea by the coordinator and the owner (2026-11-28).

**Problem (AI draft):** backlog.py decide accepts any decision on any idea: keep on a committed or dropped idea sets it back to triaged and adds a README row, and renew works on an idea that is not parked. We know it improved when decide refuses a decision that does not fit the idea's status, with one FAIL: line.

# Log

2026-11-28T12:48:32Z [capture] Captured for Jayson De los Reyes. Status inbox. Effort low, impact medium proposed by the AI.
2026-11-28T13:26:46Z [triage] Kept: decide reopens dropped or committed ideas; a script check and tests fix it. Status triaged. Effort low, impact medium confirmed by Jayson De los Reyes. Decided by Jayson De los Reyes.
