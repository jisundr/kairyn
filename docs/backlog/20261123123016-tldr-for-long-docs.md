---
title: Long stage outputs have no TL;DR
status: dropped
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

**Dropped (2026-11-25):** Each template already opens with a summary: CONCEPT `## Concept` (at most 5 sentences, older than this idea), REQUIREMENTS `## Problem statement`, DESIGN `## Approach`, and front matter `summary`. A conditional TL;DR needs stage text; `DESIGN.md` and `REQUIREMENTS.md` have 2 and 5 tokens free, and the REQUIREMENTS template (187/200) has no room.

**Notes:** Open: what counts as "very long" (a word count, a decision count), and which outputs get it. A template change re-runs the evals of each stage that fills it (`CLAUDE.md`: evals before instructions).

# Log

- 2026-11-23T12:30:16Z [capture] Created by Claude from the user's request. Status inbox, waiting for triage.
- 2026-11-23T23:02:43Z [triage] Kept. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-23T23:02:43Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Dropped: each template already opens with a summary section; no room for a conditional TL;DR. Decided by Jayson De los Reyes.
