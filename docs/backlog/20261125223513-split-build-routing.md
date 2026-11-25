---
title: Opus makes each critical decision, cheaper models carry it out
status: committed
requester: Jayson De los Reyes
date: 2026-11-26
appetite: small batch (proposed by the steward; owner to confirm)
review_by:
---

# Opus makes each critical decision, cheaper models carry it out

**Raw request:** "Change kairyn's model routing" (Jayson De los Reyes, 2026-11-26, through an Orca coordinator). The first spec moved requirements, build and the reviewer off Opus. The grill replaced it.

**Problem (confirmed by Jayson De los Reyes, 2026-11-26, grill):** Each AFK build session runs on Opus for the full slice: the test and the code. The test commit holds the decisions (test cases, interface, data shapes); the code commit only makes a red test green. close and retro only carry out decisions, on Sonnet. An orchestrating bot now reviews and approves the human-gated steps.

**Evidence:**
- `plugin/scripts/afk.py` `MODELS`: build, reviewer and review on Opus, gate on Sonnet. One build session writes both commits of a slice.
- Task 2026-11-25-first-mate-hub: the build session chose the hook data shapes and the error handling. The Opus reviewer and review found the gaps (REVIEW.md F2, F3).

**Decided (2026-11-26, grill):** One standard routing, no bot or solo switch. Opus for each critical decision. Build splits per slice: Opus writes the `test(T<n>)` commit, Sonnet writes the `feat(T<n>)` commit. close and retro go to Haiku. Details: the task's `CONCEPT.md`.

**Notes:** Related to [Split the design stage](20261124224354-split-design-stage.md), not the same idea. That idea splits design for its token budget. This one moves the technical decisions of each slice into the Opus test commit. That idea stays open.

**Task:** [docs/tasks/2026-11-26-split-build-routing/](../tasks/2026-11-26-split-build-routing/)

# Log

- 2026-11-25T22:35:13Z [capture] Created from an owner request, through an Orca coordinator. Status inbox.
- 2026-11-25T22:35:13Z [grill] Grilled on 2026-11-26: D1-D7 in the task's CONCEPT.md. Decided by Jayson De los Reyes.
- 2026-11-25T22:35:13Z [appetite] Proposed small batch (steward). Owner to confirm.
- 2026-11-25T22:35:13Z [commit] Committed to task 2026-11-26-split-build-routing. Decided by Jayson De los Reyes.
