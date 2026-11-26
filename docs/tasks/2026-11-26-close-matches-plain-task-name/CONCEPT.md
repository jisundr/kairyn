---
task: 2026-11-26-close-matches-plain-task-name
stage: grill
summary: "close.py misses committed backlog ideas that name the task in plain text, not as tasks/<task>/."
---

# Concept: close.py misses ideas that name the task in plain text

## Concept
`close.py close <task>` deletes a committed backlog idea when the idea links `tasks/<task>/`, or when the idea file slug is the task slug. If a committed idea names the task in plain text and close does not delete it, close prints `UNLINKED: <file> names <task> but does not link it; not deleted`. The close stage reports each `UNLINKED:` line as it reports `LINK:` lines. Dropped ideas use the same match: close keeps a dropped idea that links a live task or whose slug is a live task slug. Only step 6 of the close stage changes: it names `UNLINKED:` next to `LINK:`.

## Decisions
- D1: close matches the link `tasks/<task>/`, or an idea file whose slug is the task slug. It does not match the plain name anywhere else. (user: "The task link, or a file name that matches the task")
- D2: close prints an `UNLINKED:` line for a committed idea that names the task in plain text and is not deleted. The close stage reports it like `LINK:` lines. (user: "Yes, an UNLINKED line, reported like LINK lines")
- D3: dropped ideas use the same match as D1. (user: "Yes, one rule for both")

## Terms
| Term | Meaning |
|---|---|
| link | The text `tasks/<task>/` in a backlog idea. `close.py` finds it with `TASK_LINK_RE`. |
| slug | The part of a name after the date: `close-matches-plain-task-name` in both `20261126071901-close-matches-plain-task-name.md` and `2026-11-26-close-matches-plain-task-name`. |
| plain name | The task folder name without `tasks/` and the slash, for example `2026-11-26-retro`. |

## Open branches
- None.

Approval: pending
