---
title: Requirements stage misses parts of its playbook
status: committed
requester: Jayson
date: 2026-11-22
appetite:
review_by:
---

# Requirements stage misses parts of its playbook

**Raw request:** "Based on the playbook in knowledge-base. Let's create a backlog from there." (Jayson, 2026-11-22, Claude Code session) Source playbook: `knowledge-base/03 Playbooks/SDLC/01 Handling New Requirements.md`.

**Problem (AI draft, needs a human to confirm):** The requirements stage stops at exit criteria, so specs lack EARS phrasing, non-functional needs, assumptions and risks with owners, and a human approval line. Agents can then build from a spec nobody approved. We would know it improved when `REQUIREMENTS.md` ends with an approval line and lists risks with owners.

**Evidence:**
- Playbook section "Gaps to cover by hand or by extending the stage" lists these four items.
- `plugin/stages/REQUIREMENTS.md` has a 500-token budget, so all four may not fit.

**Notes:** Inference: the approval line matters most, because [design-stage](20261122080759-design-stage.md) and later stages need a gate. Evals before instructions.

# Log

2026-11-22T08:07:59Z [capture] Created from the playbook by Claude. Status inbox, waiting for triage.
2026-11-22T10:47:44Z [commit] Jayson asked for a task. Status committed, task [2026-11-22-requirements-gaps](../tasks/2026-11-22-requirements-gaps/REQUIREMENTS.md).
2026-11-22T10:57:39Z [commit] Task renamed to [2026-11-22-requirements-gaps](../tasks/2026-11-22-requirements-gaps/REQUIREMENTS.md) after #17.
