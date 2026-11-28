---
task: 2026-11-28-union-merge-restores-learnings
stage: grill
summary: "Decide how this repo merges .kairyn/learnings.md so a retro's removals hold and parallel appends stay safe."
---

# Concept: A union merge restores learnings a retro removed

## Concept
In this repo, `.gitattributes` merges `.kairyn/learnings.md` with a custom merge driver, not `union`. The driver keeps lines that either side adds and drops lines that either side removes. Thus a branch from before a retro does not restore the lines that the retro removed, and parallel appends merge with no conflict. One command, the driver script with `--install`, writes the `git config` line; without it, git does a normal merge and conflicts. A pytest proves both cases with real git merges, and consumer repos get the driver only through a new backlog idea.

## Decisions
- D1: Keep the idea, effort low, impact medium. (Jayson De los Reyes, triage)
- D2: This repo merges `.kairyn/learnings.md` with a custom merge driver in a repo script. The driver keeps lines either side adds and drops lines either side removes. Each clone sets it up with one `git config` line. Without the config, git does a normal merge and conflicts. (Q1, user)
- D3: A pytest proves the driver with real git merges in a temp repo: a retro case and a parallel-append case. (Q2, user)
- D4: The driver script in `scripts/` has an `--install` flag that writes the `git config` line. The Commands block in `CLAUDE.md` names it once. (Q3, user)
- D5: Consumer repos do not get the driver in this task. A new backlog idea (status inbox) records it. (Q4, user)

## Terms
| Term | Meaning |
|---|---|
| union merge | The `merge=union` line in `.gitattributes`: git keeps the lines of both sides and never conflicts. |
| parallel append | Two branches each add a line to `.kairyn/learnings.md`. |
| merge driver | A program git runs to merge one file, named in `.gitattributes` and defined in `git config`. |
| restored line | A line a retro removed that a merge or rebase adds again. |

## Open branches
- None

Approval: Jayson De los Reyes, 2026-11-28T11:02:25Z, "Approve" (relayed by Kairyn Steward)
