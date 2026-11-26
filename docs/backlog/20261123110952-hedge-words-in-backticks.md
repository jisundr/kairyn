---
title: Stage template does not say to put hedge words in backticks
status: parked
requester: Jayson De los Reyes
date: 2026-11-23
effort: low
impact: low
review_by: 2027-02-23
---

# Stage template does not say to put hedge words in backticks

**Raw request:** learning L15 from retro task `2026-11-23-retro`, quoted word for word:

> To name a hedge word in a stage output, put it in backticks. `checks.ste_problems` skips inline code but counts a quoted "word".

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `plugin/stages/_template.md`. Reason: `CLAUDE.md`: evals before instructions.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L15. Status inbox, waiting for triage.
2026-11-23T11:22:03Z [triage] Parked: a `_template.md` line re-runs all five stage evals. Status parked. Decided by Jayson De los Reyes.
2026-11-26T03:01:29Z [triage] Effort low, impact low confirmed by Jayson De los Reyes.
