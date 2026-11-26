---
task: 2026-11-26-close-changelog-double-name
stage: grill
summary: "close.py adds ' (<task>)' to the changelog line only when --entry does not already name the task."
---

# Concept: close writes the task name once in the changelog line

## Concept
`close.py close` adds ` (<task>)` to each changelog line, even when `--entry` already names the task. Then the line names the task twice, and a person must delete one by hand. The fix is in `plugin/scripts/close.py`, not in the `CLOSE.md` stage instructions. When `--entry` already contains the task name, close.py writes the entry as it is. Else it adds ` (<task>)` as it does now.

## Decisions
- D1: The fix goes in `plugin/scripts/close.py` itself, not in the `CLOSE.md` stage instructions. (user, 2026-11-26)
- D2: close.py skips ` (<task>)` when `--entry` already contains the task name. Else it adds it as it does now. (user, 2026-11-26)

## Terms
| Term | Meaning |
|---|---|
| task name | The task folder name, for example `2026-11-26-split-build-routing`. close.py gets it as its `<task>` argument. |
| suffix | The text ` (<task>)` that close.py adds after the entry. |

## Open branches
- None. Source: backlog idea `20261125235010-close-changelog-double-task-name`, triaged small batch, Next.

Approval: Jayson De los Reyes, 2026-11-26T00:58:13Z, "Grill answers: the fix goes in close.py; skip ' (<task>)' when --entry already contains the task name, else add it as today"
