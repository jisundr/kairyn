---
title: Stages do not gate on approval and hand off to the next stage
status: triaged
requester: Jayson
date: 2026-11-23
appetite: big batch
review_by: 2027-02-23
---

# Stages do not gate on approval and hand off to the next stage

**Raw request:** "Or we can also make gates as well for concept doc. if aligned, approved and proceed to requirements" (Jayson, 2026-11-23)

**Problem (confirmed by Jayson De los Reyes, 2026-11-25):** Grill ends with a chat "yes" only a log line records, then the user types `/kairyn:requirements`. Requirements also stops after approval. Improved when every gated stage records an approval line and that approval starts the next stage as its own skill.

**Evidence:** `GRILL.md` step 7 stops on a confirm; `CONCEPT.md` has no `Approval:` line. ADR 0002: the user runs requirements. ADR 0001 and `checks.approval_problems` define the line; design D3 adds it.

**Decided (2026-11-25):** Spike first. Start the next stage only on explicit approval words (ADR 0001). One rule for grill → requirements and requirements → design, through `_approval.md`.

**Spike (2026-11-25):** Scratch repo, `claude -p` 2.1.331, `--model haiku`. Skill `first` (`model: sonnet`) calls the Skill tool for `second` (`model: opus`). JSONL `message.model`: typed `/first` ran all turns, `second`'s too, on `claude-sonnet-5-5`. Controls: typed `/second` ran on opus; the Skill tool from the session ran on haiku. $0.29 in all.
**Answer: a chained skill runs on the caller's model.** `model:` holds only for a skill the user types. A handoff that calls the next skill would run requirements on grill's Sonnet, not Opus. The handoff must have the user type the next command. ADR 0004 gets this at close.

**Notes:** Changes the grill eval end state and ADR 0002.

# Log

- 2026-11-23T00:42:58Z [capture] Created from a chat request by Claude. Status inbox.
- 2026-11-23T09:50:02Z [triage] Kept: design has the gate; grill has no approval line yet. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-23T09:55:02Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Kept, problem confirmed. Not Next: spike first. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [appetite] Set to big batch (was small). Decided by Jayson De los Reyes.
- 2026-11-25T09:07:16Z [spike] Chained skill runs on the caller's model. Run by Claude.
