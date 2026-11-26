# 26. Close matches a backlog idea to its task by link or file slug, not by plain name

Date: 2026-11-26

## Status
Accepted

## Context
Task 2026-11-26-close-matches-plain-task-name. `close.py close <task>` deleted a committed backlog idea only when the idea had the text `tasks/<task>/`. The idea of task `2026-11-26-upgrade-overwrites-running-stages` named its task in plain text only. Close kept it, printed no warning, and a person deleted it by hand. Other ideas name a task in plain text only as their origin, for example `init-ships-union-merge`.

## Decision
- Close matches an idea to a task by the link `tasks/<task>/`, or when the idea file slug is the task slug. It does not match the plain name for a delete (D1, R1, R2).
- A committed idea that has the full task name as a whole word, but no match, is kept. Close prints `UNLINKED: <file> names <task> but does not link it; not deleted`, and the close stage reports it like `LINK:` lines (D2, R3, R6).
- Dropped ideas use the same match to find a live task (D3, R4, R5).

## Consequences
- An idea that only cites a task as its origin is never deleted with that task.
- A committed idea named in plain text, with another slug, still needs a hand delete. Close now names it.
- Two tasks with the same slug on different dates both match one committed idea (K1).
