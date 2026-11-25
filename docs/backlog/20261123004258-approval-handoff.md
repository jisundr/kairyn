---
title: Stages do not gate on approval and hand off to the next stage
status: committed
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

**Spike (2026-11-25):** A chained skill runs on the caller's model; `model:` holds only for a skill the user types. So the handoff has the user type the next command. Details: ADR 0004.

**Notes:** Changed the grill eval end state and ADR 0002.

# Log

- 2026-11-23T00:42:58Z [capture] Created from a chat request by Claude. Status inbox.
- 2026-11-23T09:50:02Z [triage] Kept: design has the gate; grill has no approval line yet. Status triaged. Decided by Jayson De los Reyes.
- 2026-11-23T09:55:02Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [triage] Kept, problem confirmed. Not Next: spike first. Decided by Jayson De los Reyes.
- 2026-11-25T08:49:41Z [appetite] Set to big batch (was small). Decided by Jayson De los Reyes.
- 2026-11-25T09:07:16Z [spike] Chained skill runs on the caller's model. Run by Claude.
- 2026-11-25T10:05:30Z [next] Moved to Next, spike answered. Decided by Jayson De los Reyes.
- 2026-11-25T10:05:30Z [close] Shipped in PRNUM: grill approval gate, `_approval.md` names the next command, ADR 0002 and 0004 updated, 0.14.0. Delete at release. From an Orca coordinator dispatch.
