---
task: 2026-11-26-logs-as-bullet-lists
stage: requirements
summary: "Scripts, stage rules and the STATE.md template write each new STATE.md log entry as a markdown bullet; old entries stay."
---

# Requirements: write STATE.md log entries as bullets

## Problem statement
A `STATE.md` log entry is a plain line: `<timestamp> [<stage>] <text>`. Entries have no blank line between them. Markdown joins them into one paragraph, so GitHub, VS Code and pull requests show the log as one block of text. Backlog files already write log entries as bullets.

## Scope
In: `afk.py` `update()`, the log rule in `_template.md`, `plugin/templates/STATE.md`, this repo's `.kairyn/` copies of the last two (D1); the log line in `close.py` `record-merge` (A1); the log format in `.harness/workflows/task-lifecycle.md` (CLAUDE.md); tests for each script writer (request)
Out: existing log entries (D2); the milestones log `.session/milestones.log` (D1); `.kairyn/learnings.md` and backlog files, which already use bullets; any reader of log entries (none exists)

## Requirements
- R1: When `afk.py` appends a log entry to `STATE.md`, it shall write `- <timestamp> [<stage>] <text>`. (D1)
- R2: When `close.py record-merge` appends its log entry to `STATE.md`, it shall write `- <timestamp> [review] Merged by hand: ...`. (A1)
- R3: The log rule in `_template.md` shall tell each stage to append `- <timestamp> [<stage-name>] <summary of what happened>`. (D1)
- R4: The `STATE.md` template shall show its first log entry in bullet form. (D1)
- R5: The `.kairyn/` copies of `_template.md` and `STATE.md` shall be the same as their `plugin/` sources. (D1, A2)
- R6: The scripts shall not change log entries that exist in a `STATE.md`. (D2)
- R7: The task-lifecycle harness doc shall show the bullet form of a log entry. (CLAUDE.md)
- R8: The milestones log shall keep its plain form. (D1)

## Non-functional needs
- Accessibility: a rendered log shows one entry per line. (request)
- Performance: not applicable: one string per log entry.
- Security: not applicable: no new input or command.
- Observability: not applicable: the log entry text does not change.

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | `close.py record-merge` (merged in #64, after the idea) is a second script writer. The concept "each new log entry is a bullet" covers it. | Jayson De los Reyes |
| A2 | assumption | `/kairyn:upgrade` carries the template change to user repos, as for any stage file. The plugin version and `release-hashes.json` change as the repo rules require. | Jayson De los Reyes |
| K1 | risk | A task open during the upgrade has a log with both forms (D2). Nothing reads log entries, so nothing breaks. | Jayson De los Reyes |
| K2 | risk | Stage evals that depend on `_template.md` can fail if a model copies the old form from an old log. D3 runs them to find out. | Kairyn Steward |
| K3 | dependency | The eval suites the selector picks pass once after the build (D3). | Kairyn Steward |

## Acceptance criteria
- [ ] A test runs `afk.py` `update()` on a `STATE.md` and finds the new entry as `- <timestamp> [<stage>] <text>`. (R1)
- [ ] A test runs `close.py record-merge` with a stub `gh` and finds its entry in bullet form. (R2)
- [ ] `_template.md` and `STATE.md` in `plugin/` show the bullet form, and `.kairyn/` copies match them byte for byte. (R3, R4, R5)
- [ ] A test with a plain entry already in `STATE.md` finds it unchanged after `update()` and after `record-merge`. (R6)
- [ ] `task-lifecycle.md` shows the bullet form, and `/kairyn:check` passes. (R7)
- [ ] `milestones.py` and its tests have no change. (R8)
- [ ] `uv run pytest` and `claude plugin validate plugin` pass, and the selector-picked evals pass once (D3). (R1, R3)

## Open questions and answers
- None.

Approval: Jayson De los Reyes, 2026-11-26T07:00:57Z, "Approve"
