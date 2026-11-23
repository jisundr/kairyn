---
title: Long stage outputs have no TL;DR
status: triaged
requester: Jayson De los Reyes
date: 2026-11-23
appetite: small batch
review_by:
---

# Long stage outputs have no TL;DR

**Raw request:** "Also, please add TLDR or executive summary for doc that is very long" … "Make a backlog I mean" (Jayson, 2026-11-23, Claude Code session, grill of task `2026-11-23-build-stage`).

**Problem (AI draft, needs a human to confirm):** A long stage output, such as a `CONCEPT.md` with 20 decisions, makes the reader scan every section to get the gist before an approval. We would know it improved when each long output opens with a short TL;DR under its title.

**Evidence:**
- The build-stage task's `CONCEPT.md` held 20 decisions; a TL;DR was added there by hand. Exit deleted the folder; git history keeps it.
- No template in `plugin/templates/` has a TL;DR line. The front matter `summary` is one line for agents, not a reader summary.

**Notes:** Open: what counts as "very long" (a word count, a decision count), and which outputs get it. A template change re-runs the evals of each stage that fills it (`CLAUDE.md`: evals before instructions).

# Log

2026-11-23T12:30:16Z [capture] Created by Claude from the user's request. Status inbox, waiting for triage.
2026-11-23T23:02:43Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
2026-11-23T23:02:43Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
