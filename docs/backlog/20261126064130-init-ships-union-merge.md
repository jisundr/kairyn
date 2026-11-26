---
title: Init ships the learnings.md union merge
status: triaged
requester: Jayson De los Reyes
date: 2026-11-26
effort: medium
impact: medium
review_by: 2027-02-23
---

# Init ships the learnings.md union merge

**Raw request:** capture "init ships the learnings.md union merge for every repo" as a new inbox idea, outside the upgrade-overwrites-running-stages batch (owner, grill Q4, 2026-11-26, through Orca).

**Problem (not confirmed):** Each stage appends to `.kairyn/learnings.md`, so parallel task branches can conflict on it at a merge or rebase. This repo stops that with `.kairyn/learnings.md merge=union` in `.gitattributes` (cb1f43f). Other kairyn repos do not get that line.

**Evidence:**
- `.gitattributes` in this repo has the line and a comment. `plugin/` ships no `.gitattributes`.
- The union note in this repo's `running-stages.md` was lost on three upgrades (PR #48, #50, #54), because the shipped doc does not have it.

**Notes:** Inference: init can append the line to `.gitattributes`, and it must never overwrite a user's file. The shipped `running-stages.md` can then name the merge for every repo.

# Log

- 2026-11-26T06:41:30Z [capture] Created from the owner's grill answer Q4 in task 2026-11-26-upgrade-overwrites-running-stages. Status inbox, waiting for triage. Effort medium, impact medium proposed by the AI.
- 2026-11-26T07:33:12Z [triage] Kept, problem not confirmed yet. Not Next. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-26T07:33:12Z [triage] Effort medium, impact medium confirmed by Jayson De los Reyes.
