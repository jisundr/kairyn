---
title: A merge driver for learnings.md in consumer repos
status: inbox
requester: Jayson De los Reyes
date: 2026-11-28
effort: medium
impact: low
review_by:
---

# A merge driver for learnings.md in consumer repos

**Problem:** In a consumer repo, two task branches that each append to `.kairyn/learnings.md` conflict on a merge or rebase. A person must keep both lines by hand.

**Idea:** Ship this repo's `scripts/merge_learnings.py` driver with the plugin. Init writes the `.gitattributes` line, and a command writes the `git config` entry. A union merge is not an option: it restores lines a retro removed (init-ships-union-merge was dropped for this reason).

**Cost:** It changes `plugin/` and init, so it needs evals and a version bump. Each clone needs the `git config` entry. Without it, git merges as text and conflicts.

# Log

- 2026-11-28T11:07:48Z [capture] From task 2026-11-28-union-merge-restores-learnings (D5), approved by Jayson De los Reyes. Status inbox, waiting for triage. Effort medium, impact low proposed by the AI.
