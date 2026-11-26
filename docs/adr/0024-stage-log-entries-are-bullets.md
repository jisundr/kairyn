# 24. STATE.md log entries are bullets; old entries stay

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-logs-as-bullet-lists. A `STATE.md` log entry was a plain line: `<timestamp> [<stage>] <text>`. Entries have no blank line between them, so markdown joined them into one paragraph. GitHub, VS Code and pull requests showed the log as one block of text. Backlog files already wrote log entries as bullets.

## Decision
- Each new log entry is a bullet: `- <timestamp> [<stage>] <text>`. `afk.py` `update()`, the `_template.md` log rule, the `STATE.md` template and their `.kairyn/` copies change (D1).
- `close.py record-merge` also writes a bullet entry. It is a second script writer of log entries (A1).
- Log entries that exist do not change. Only new entries are bullets, so an open task can have a log with both forms (D2).
- The milestones log (`.session/milestones.log`) keeps its plain form. It is a `.log` file, not markdown (D1).
- The eval checks (`evals/checks.py` `log_line_re`) accept both forms.

## Consequences
- An open task after the upgrade has a mixed log. No script reads log entries, so nothing breaks (K1).
- A model can copy the plain form from the old entries of a log. In the eval run, 3 of 10 model-routing runs did this (K2).
- A future change to the log format must also change `log_line_re`; `task-lifecycle.md` names it.
