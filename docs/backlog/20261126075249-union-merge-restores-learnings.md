---
title: A union merge restores learnings a retro removed
status: committed
requester: Jayson De los Reyes
date: 2026-11-26
effort: low
impact: medium
review_by:
---

# A union merge restores learnings a retro removed

**Learning (word for word):**

- 2026-11-26 [close] `.gitattributes` merges `.kairyn/learnings.md` by `union`, so a union merge keeps lines one side deleted. The retro of 2026-11-26 (97e81eb) emptied learnings.md; the merge of PR #66, from a branch based before it, added 8 of its removed lines again (2026-11-26-logs-as-bullet-lists).

**Evidence (2026-11-28, task 2026-11-28-init-ships-union-merge):**
- PR #66 merged on GitHub with no conflict, because its branch was already rebased onto 0ffabbe, after the 97e81eb retro. The lines came back at that local rebase, not at the GitHub merge.
- Retro case (base = learnings.md before 97e81eb, ours = after it, theirs = before it plus one new line): `git merge-file` conflicts (exit 1); `git merge-file --union` gives all 13 removed lines back with no conflict.
- Parallel append case (two branches each add one line): plain merge conflicts; union keeps both lines.
- init-ships-union-merge was dropped for this reason (2026-11-28). Consumer repos get no union merge.

# Log

- 2026-11-26T07:52:49Z [capture] From the 2026-11-26 second retro, approved by Jayson De los Reyes. Status inbox, waiting for triage. Effort low, impact medium proposed by the AI.
- 2026-11-28T10:52:54Z [triage] Effort low, impact medium confirmed by Jayson De los Reyes (relayed by Kairyn Steward). Status triaged.
- 2026-11-28T10:52:54Z [commit] Task docs/tasks/2026-11-28-union-merge-restores-learnings/ started with grill. Status committed.
