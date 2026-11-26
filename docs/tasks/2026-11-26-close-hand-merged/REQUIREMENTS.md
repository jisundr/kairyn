---
task: 2026-11-26-close-hand-merged
stage: requirements
summary: "A close.py command records a hand merge from the merged PR found through gh; the close stage runs it when STATE.md is not done."
---

# Requirements: close records a hand merge from the merged pull request

## Problem statement
A task built and merged by hand keeps `status: in-progress` and has no `REVIEW.md` with a `Decision:` line. Only `afk.py` `decide` (`/kairyn:review approve`) records a merge. So `close.py check` fails until the closing agent edits `STATE.md` and writes `REVIEW.md` by hand. That happened in the last three closes: #49, #51 and #56.

## Scope
In: a new `close.py` command (the record command), `plugin/stages/CLOSE.md` and its `.kairyn/stages/` copy, `plugin/skills/close/SKILL.md` if needed, `tests/test_close.py`, the close eval, `.harness/workflows/task-lifecycle.md` (D1-D5)
Out: `afk.py`; a `check` that accepts a merged pull request in place of the `Decision:` line (D1 chose a command); prompts to the user (D5); the merge itself

## Requirements
- R1: When the record command runs on a task whose `STATE.md` status is not `done` and it finds the task's merged pull request, the close script shall set `status: done`, `stage: review`, `review: done` in `stages` and `updated`, and log one line that names the pull request, who merged it and when. (D1, A2)
- R2: When the record command records a merge, the close script shall write `Decision: <name>, <merged-at>, "merged PR #<n>"` in `REVIEW.md`: in place of a `Decision: pending` line, or in a new `REVIEW.md` if none exists. (D1, D2, A3)
- R3: The close script shall take `<name>` from the pull request's merged-by name, or its login when the name is empty, and `<merged-at>` from its merge time in UTC. (D2, A4)
- R4: When `STATE.md` names a pull request as `PR #<n>`, the close script shall use the last one it names. (D4, A1)
- R5: When `STATE.md` names no pull request, the close script shall search the merged pull requests by the task's branch name. (D4, A5)
- R6: If `gh` is missing or fails, the named pull request is not merged, no merged pull request matches, or more than one matches, the close script shall print `FAIL: <what is missing>`, exit 1, change no file and not prompt. (D5, A6)
- R7: When the record command runs on a task whose `STATE.md` status is `done`, the close script shall change no file and exit 0. (A7)
- R8: When the close stage starts and the task's `STATE.md` status is not `done`, the close stage shall run the record command before `check`, and on `FAIL` report it and stop. (D3)
- R9: The task-lifecycle harness doc shall say how close records a hand merge. (CLAUDE.md)

## Non-functional needs
- Accessibility: not applicable: a command-line script.
- Performance: not applicable: at most two `gh` calls per run.
- Security: the script runs `gh` with an argument list, not a shell, as `afk.py` does. (A8)
- Observability: the record command prints one line that names the pull request, the name and the time it recorded. (D2)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | "`STATE.md` names the pull request" means a `PR #<n>` in its text. The last one is the newest log line, the task's own pull request. | Jayson De los Reyes |
| A2 | assumption | Other `stages` values (for example `build: pending`) stay as they are. Only `review` changes. | Jayson De los Reyes |
| A3 | assumption | A new `REVIEW.md` has the output front matter, a title and the `Decision:` line only: no review ran. | Jayson De los Reyes |
| A4 | assumption | The name is the merger's GitHub name, which can differ from `git config user.name`. | Jayson De los Reyes |
| A5 | assumption | The task's branch name is `kairyn/<task>` (an AFK run), or a branch whose last `/` part is the task folder name or its slug (for example `jisundr/close-changelog-double-name`). | Jayson De los Reyes |
| A6 | assumption | More than one match fails and names each pull request, so the user can add `PR #<n>` to `STATE.md`. | Jayson De los Reyes |
| A7 | assumption | The record command is safe to run on any task, so the stage can run it with no extra check. | Jayson De los Reyes |
| A8 | assumption | `KAIRYN_GH` overrides the `gh` path, as in `afk.py`, so tests and evals use a stub. | Jayson De los Reyes |
| K1 | risk | A `STATE.md` whose last `PR #<n>` is another pull request records the wrong merge. The logged line names the pull request, so the user sees it before the close commit. | Jayson De los Reyes |
| K2 | dependency | `gh` is installed and signed in to the repo's GitHub remote. | User of the repo |

## Acceptance criteria
- [ ] A test with a stub `gh` and an in-progress task that names `PR #12` gets `status: done`, `stage: review`, `review: done`, a log line, and `check` prints `OK`. (R1, R4)
- [ ] A test with no `REVIEW.md` gets a new one with the stub's name, merge time and `"merged PR #12"`. A test with `Decision: pending` gets that line replaced. (R2)
- [ ] A test with an empty merged-by name gets the login. (R3)
- [ ] A test with no `PR #<n>` in `STATE.md` finds the pull request by branch `kairyn/<task>` and by a branch that ends in the slug. (R5)
- [ ] Tests with no `gh`, an open pull request, no match and two matches each print `FAIL:` with the cause, exit 1 and leave the task files unchanged. (R6)
- [ ] A test on a done task changes no file and exits 0. (R7)
- [ ] `CLOSE.md` (both copies) runs the record command before `check` when the status is not `done`, and the close eval closes a hand-merged task with a stub `gh`. (R8)
- [ ] `task-lifecycle.md` names the record command, and `/kairyn:check` passes. (R9)

## Open questions and answers
- Q1: How does the command find the task's branch for a hand build, whose branch name is free? A: As A5; the user adds `PR #<n>` to `STATE.md` when no branch matches. The owner confirms. (agent, 2026-11-26)

Approval: pending
