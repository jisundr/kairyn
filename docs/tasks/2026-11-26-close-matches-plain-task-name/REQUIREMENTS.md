---
task: 2026-11-26-close-matches-plain-task-name
stage: requirements
summary: "close.py also deletes a committed idea whose file slug is the task slug, and prints UNLINKED for one that names the task in plain text."
---

# Requirements: close.py misses ideas that name the task in plain text

## Problem statement
`close.py close <task>` deletes a committed backlog idea only if the idea text has `tasks/<task>/`. The idea of task `2026-11-26-upgrade-overwrites-running-stages` named the task in plain text only. Close kept it, and a person deleted it and its `README.md` row by hand (commit 63977db). Close printed no warning.

## Scope
In: the backlog match in `close.py` for committed and dropped ideas (D1, D3). An `UNLINKED:` line (D2). Step 6 of `plugin/stages/CLOSE.md` (D2).
Out: a match on the plain task name for a delete (D1). Changes to other stages or to the idea template.

## Requirements
- R1: When `close <task>` runs, the close script shall delete each committed idea that has the text `tasks/<task>/`. (D1)
- R2: When `close <task>` runs, the close script shall delete each committed idea whose file slug is the slug of `<task>`. (D1)
- R3: If a committed idea has the plain task name and R1 and R2 do not match it, then the close script shall keep the idea and print `UNLINKED: <file> names <task> but does not link it; not deleted`. (D2)
- R4: When `close <task>` runs, the close script shall keep each dropped idea that links a live task or whose file slug is the slug of a live task. (D3)
- R5: When `close <task>` runs, the close script shall delete each dropped idea that R4 does not keep. (D3)
- R6: The close stage shall report each `UNLINKED:` line as it reports each `LINK:` line. (D2)
- R7: When the close script deletes an idea by R2, the close script shall remove the idea row from `docs/backlog/README.md`. (D1)

## Non-functional needs
- Accessibility: not applicable: a CLI line.
- Performance: not applicable: no source states a need.
- Security: not applicable: no source states a need.
- Observability: each `UNLINKED:` line names the file and the task. (D2)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A file slug is the file name without its 14-digit timestamp, the dash and `.md`. A task slug is the task name without `YYYY-MM-DD-`. | design |
| A2 | assumption | A live task is a folder in `docs/tasks/` other than `<task>`, as today. | design |
| A3 | assumption | The plain task name in R3 is the full task name, `YYYY-MM-DD-<slug>`, as a whole word. | design |
| K1 | risk | Two tasks with the same slug on different dates. Close then deletes a committed idea of the older task. | Jayson De los Reyes |
| K2 | risk | R6 changes `plugin/stages/CLOSE.md`, so the close eval must run. | Jayson De los Reyes |

## Acceptance criteria
- [ ] A test: a committed idea with `tasks/<task>/` is deleted. (R1)
- [ ] A test: a committed idea with the task slug as its file slug, and no link, is deleted, and its `README.md` row goes. (R2, R7)
- [ ] A test: a committed idea with another slug that names the task in backticks is kept, and close prints its `UNLINKED:` line. (R3)
- [ ] A test: a committed idea that names a different task, which has the same date, prints no `UNLINKED:` line. (R3)
- [ ] A test: a dropped idea whose file slug is a live task slug is kept. A dropped idea with no live link and no live slug is deleted. (R4, R5)
- [ ] `plugin/stages/CLOSE.md` step 6 names `UNLINKED:` next to `LINK:`, and the close eval passes. (R6)

## Open questions and answers
- None.

Approval: Jayson De los Reyes, 2026-11-26T07:43:37Z, "Approve"
