---
title: Parallel tasks can conflict on learnings.md
status: inbox
requester: Jayson
date: 2026-11-23
appetite:
review_by:
---

# Parallel tasks can conflict on learnings.md

**Raw request:** "review the knowledge base again" (Jayson, 2026-11-23, Claude Code session) Source playbook: `knowledge-base/03 Playbooks/Agents/05 Running Parallel Agents.md`.

**Problem (AI draft, needs a human to confirm):** The playbook runs one task per Git worktree and hands off through Git. Every kairyn stage appends to `.kairyn/learnings.md`, so two task branches that both append at the end of the file conflict on merge. We would know it improved when two branches that each add a learning merge with no conflict.

**Evidence:**
- `plugin/stages/_template.md:56`: every stage appends to `.kairyn/learnings.md`.
- No `.gitattributes` in this repo, and init installs none.
- Not seen yet: no recorded conflict. Inference from the playbook.

**Notes:** Inference: small appetite. A `merge=union` line in `.gitattributes` for `learnings.md` may be enough. Check `CHANGELOG.md` too: exit writes it after merge, so the risk is lower there.

# Log

2026-11-23T09:39:00Z [capture] Created from the playbook by Claude. Status inbox, waiting for triage.
