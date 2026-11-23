---
title: A forked eval agent that returns early kills its run
status: inbox
requester: Jayson De los Reyes
date: 2026-11-23
appetite:
review_by:
---

# A forked eval agent that returns early kills its run

**Raw request:** learning L23 from retro task `2026-11-23-retro`, quoted word for word:

> A forked `/run-evals` agent that returns before `== eval summary ==` kills its run. Check for `summary.md` before you trust the report.

**Problem (AI draft, needs a human to confirm):** The rule has no file an agent reads at the right time. Home: `.claude/agents/eval-runner.md`. Reason: `CLAUDE.md`: evals before instructions.

# Log

2026-11-23T11:09:52Z [capture] Created by retro from `.kairyn/learnings.md` L23. Status inbox, waiting for triage.
