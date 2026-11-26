---
task: 2026-11-26-logs-as-bullet-lists
stage: grill
summary: "Write each STATE.md log entry as a markdown bullet, so a rendered log shows one line per entry."
---

# Concept: Write log sections as bullet lists

## Concept
Each new log entry in a task's `STATE.md` is a markdown bullet: `- <timestamp> [<stage>] <text>`. Then GitHub and VS Code show one line per entry, as backlog files do now. `afk.py` `update()`, the log rule in `_template.md` and the `STATE.md` template change, in `plugin/` and in this repo's `.kairyn/`. Old log entries and the milestones log stay as they are. After the build, the eval suites that the selector picks run once, after the coordinator approves the list and the cost.

## Decisions
- D1: Change `afk.py` `update()`, the log rule in `_template.md`, `plugin/templates/STATE.md` and this repo's `.kairyn/` copies. The milestones log (`.session/milestones.log`) stays in plain form. (Jayson De los Reyes)
- D2: Do not change log entries that exist. Only new entries use bullet form, so an open task can have a log with both forms. (Jayson De los Reyes)
- D3: Run the eval suites the selector picks for the changed files, once, after the build. Ask the supervisor first with the list and the cost. (Kairyn Steward, the coordinator who picks evals)

## Terms
| Term | Meaning |
|---|---|
| log entry | One line under `# Log` in `STATE.md`: a timestamp, a `[<stage>]` tag and text. |
| bullet form | A log entry that starts with `- `: `- <timestamp> [<stage>] <text>`. |
| plain form | A log entry with no `- `: the form in use now. |

## Open branches
- None

Approval: Jayson De los Reyes, 2026-11-26T06:45:30Z, "Approve"
