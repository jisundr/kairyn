---
title: No check that agents follow context pointers
status: inbox
requester: Jayson
date: 2026-11-22
appetite:
review_by:
---

# No check that agents follow context pointers

**Raw request:** "Based on the playbook in knowledge-base. Let's create a backlog from there." (Jayson, 2026-11-22, Claude Code session) Source playbook: `knowledge-base/03 Playbooks/Agents/02 Writing Agent Instruction Files.md`.

**Problem (AI draft, needs a human to confirm):** kairyn installs a lean `CLAUDE.md` block with pointers to `.harness/` docs, but nothing checks that an agent reads the right doc for a task, or that the always-loaded prefix stays the same across runs. We would know it improved when an eval shows the agent opens the pointed doc for sample tasks.

**Evidence:**
- Already covered: size budgets (`budgets.yml`), `read_when` headers, the generated index (`harness_docs.py`).
- Not covered: playbook step 8 (follow the pointer) and step 6 (no dynamic values in the prefix).

**Notes:** Partly done. Inference: small appetite.

# Log

2026-11-22T08:07:59Z [capture] Created from the playbook by Claude. Status inbox, waiting for triage.
