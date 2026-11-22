---
title: Requirements stage does not grill the user
status: dropped
requester: Jayson
date: 2026-11-22
appetite:
review_by:
---

# Requirements stage does not grill the user

**Raw request:** "how to trigger grill?" … "In this project" … "add task" (Jayson, 2026-11-22, Claude Code session)

**Problem (AI draft, needs a human to confirm):** The requirements stage asks open questions only when the repo cannot answer them, all at once. Nothing walks the user through the design one question at a time, so gaps stay hidden until later stages. We would know it improved when an eval shows the stage asks one question per message, each with a recommended answer, and records every answer in `REQUIREMENTS.md` before it writes the scope.

**Evidence:**
- `plugin/stages/REQUIREMENTS.md` step 4: "ask the user only those you cannot resolve from the repo".
- No `grill` command, stage or step exists in `plugin/`.
- Prior art: the loopza `requirements` loop grills one question per message with a recommended answer and keeps open questions on disk, so a context reset loses nothing.
- `plugin/stages/REQUIREMENTS.md` is at 498/500 tokens.

**Notes:** Inference: an optional stage (like `MODEL-ROUTING`) or a flag fits better than more steps in a full file. Non-interactive runs need a fallback: take the recommended answers and label them as assumptions. Relates to [requirements-gaps](20261122080759-requirements-gaps.md). Evals before instructions.

# Log

2026-11-22T10:41:50Z [capture] Created from a chat request by Claude. Status inbox, waiting for triage.
2026-11-22T10:47:44Z [commit] Jayson asked for a task. Status committed, task [2026-11-22-requirements-grill](../tasks/2026-11-22-requirements-grill/REQUIREMENTS.md).
2026-11-22T10:57:39Z [drop] #17 shipped grilling as the optional grill stage. The rounds change moves to [grill-rounds](20261122105739-grill-rounds.md).
