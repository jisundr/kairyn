---
task: 2026-11-26-close-matches-plain-task-name
stage: design
summary: "Option A: close.py matches a task by link or file slug, prints UNLINKED for a plain name; CLOSE.md step 6 names UNLINKED; patch bump."
---

# Design: close.py misses ideas that name the task in plain text

## Approach
Option A. It changes one function in `close.py` and one line in `CLOSE.md`, and meets R1-R7. The slug and the plain name come from the task name, so close needs no new input.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | In `close.py`, a helper `tasks_of(path, text, root)` returns the tasks an idea links, plus the task whose slug is the file slug and whose folder exists or is `<task>`. `closed_backlog` uses it for committed and dropped ideas. `cmd_close` prints `UNLINKED:` for a committed idea that has the plain task name and no match. | About 25 lines in `close.py`, 6 tests, 1 line in `CLOSE.md`, close eval (about $8). | Low. Only `close` changes. |
| B | Option A, and the grill and requirements stages also write `**Task:** [docs/tasks/<task>/](...)` in the idea. | Option A, plus two stage edits and the grill and requirements evals. | The stage edits can still be missed, and the evals cost more. |

## Tasks
- T1: Tracer bullet: a committed idea with the task slug as its file slug, and no link, is deleted with its `README.md` row. Add `slug_of(name)` (strip `^\d{14}-` from a file stem, `^\d{4}-\d\d-\d\d-` from a task) and `tasks_of`. Files: `tests/test_close.py`, `plugin/scripts/close.py`. Done: `uv run pytest tests/test_close.py` exits 0.
- T2: Dropped ideas use `tasks_of`: keep one whose slug names a live task, delete one with no live link and no live slug. Files: `tests/test_close.py`, `plugin/scripts/close.py`. after: T1. Done: `uv run pytest tests/test_close.py` exits 0.
- T3: `UNLINKED:` for a committed idea that has `<task>` as a whole word (`(?<![\w-])<task>(?![\w-])`) and no match. Update the docstring. Files: `tests/test_close.py`, `plugin/scripts/close.py`. after: T1. Done: `uv run pytest tests/test_close.py` exits 0.
- T4: `CLOSE.md` step 6: "Report each `LINK:` as a link to fix, and each `UNLINKED:` as an idea to delete by hand." Bump the plugin version to the next patch, add the changelog line, update `.harness` docs if one names the match. Files: `plugin/stages/CLOSE.md`, `plugin/.claude-plugin/plugin.json`, `CHANGELOG.md`. after: T3. Done: `uv run pytest && claude plugin validate plugin` exits 0.
- T5: Run the close eval after the owner says yes to its cost. Files: none. after: T4. Done: `/run-evals close` reports PASS.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 a linked committed idea is deleted | T1 | `test_close_deletes_linked_and_dropped_backlog_files_only` (already there) |
| AC2 a slug-matched committed idea and its row are deleted | T1 | `test_close_deletes_a_committed_idea_named_by_slug` |
| AC3 a plain name with another slug is kept and printed | T3 | `test_close_prints_unlinked_for_a_plain_task_name` |
| AC4 a different task on the same date prints no line | T3 | `test_close_prints_no_unlinked_for_a_longer_task_name` |
| AC5 dropped ideas keep a live slug, delete the rest | T2 | `test_close_keeps_a_dropped_idea_named_by_a_live_slug` |
| AC6 `CLOSE.md` names `UNLINKED:`, close eval passes | T4, T5 | `/run-evals close` |

Approval: Jayson De los Reyes, 2026-11-26T07:49:59Z, "Approve"
