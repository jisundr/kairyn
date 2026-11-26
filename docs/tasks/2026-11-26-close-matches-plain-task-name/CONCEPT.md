---
task: 2026-11-26-close-matches-plain-task-name
stage: grill
summary: "close.py misses committed backlog ideas that name the task in plain text, not as tasks/<task>/."
---

# Concept: close.py misses ideas that name the task in plain text

## Concept
Not confirmed yet.

## Decisions
- None yet.

## Terms
| Term | Meaning |
|---|---|
| link | The text `tasks/<task>/` in a backlog idea. `close.py` finds it with `TASK_LINK_RE`. |
| plain name | The task folder name without `tasks/` and the slash, for example `2026-11-26-retro`. |

## Open branches
- Q1: what close matches. Q2: what close does with an unmatched idea. Q3: dropped ideas.

Approval: pending
