---
title: Stages do not gate on approval and hand off to the next stage
status: triaged
requester: Jayson
date: 2026-11-23
appetite: small batch
review_by:
---

# Stages do not gate on approval and hand off to the next stage

**Raw request:** "why not convert grill session to requirement?" … "automatically?" … "Or we can also make gates as well for concept doc. if aligned, approved and proceed to requirements" (Jayson, 2026-11-23, Claude Code session)

**Problem (AI draft, needs a human to confirm):** Grill ends with a chat "yes" that only a log line records, and the user must then type `/kairyn:requirements`. Requirements also stops after approval. We would know it improved when every gated stage records an approval line in its output, and that approval starts the next stage as its own skill.

**Evidence:**
- `GRILL.md` step 7: "Stop only when the user confirms". `CONCEPT.md` has no `Approval:` line.
- ADR 0002: "the user runs requirements on that folder".
- ADR 0001 and `checks.approval_problems` already define the approval line for requirements.
- Task 2026-11-23-design-stage (D3) adds the same gate to design.

**Notes:** One rule for grill → requirements and requirements → design. Unknown: does a skill started from another skill run on its own `model:`? Prove it with an eval first. Changes the grill eval end state and ADR 0002. `GRILL.md` is at 498/500 tokens.

# Log

2026-11-23T00:42:58Z [capture] Created from a chat request by Claude. Status inbox, waiting for triage.
2026-11-23T09:50:02Z [triage] Kept: design has the gate; grill has no approval line yet. Status triaged. Decided by Jayson De los Reyes.
2026-11-23T09:55:02Z [appetite] Set to small batch. Decided by Jayson De los Reyes.
