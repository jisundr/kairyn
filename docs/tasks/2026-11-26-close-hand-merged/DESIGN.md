---
task: 2026-11-26-close-hand-merged
stage: design
summary: "Option A: close.py record-merge reads the merged PR through gh and writes STATE.md and REVIEW.md; CLOSE.md step 1 always runs it before check."
---

# Design: close records a hand merge from the merged pull request

## Approach
Option A. `close.py` gets a command `record-merge <task> [--pr <n>]`. It exits 0 with `OK: <task> is done` when `STATE.md` says `status: done`, before it calls `gh` (R7). Else it finds the pull request: `--pr` (R10), else the last `PR #<n>` in `STATE.md` (R4), else `gh pr list --state merged --limit 200 --json number,headRefName` and the heads that are `kairyn/<task>` or whose last `/` part is the task folder name or its slug (R5). A named pull request comes from `gh pr view <n> --json number,state,mergedAt,mergedBy`. Any problem prints `FAIL: <cause>` and exits 1 before a file is written (R6). Then it writes `REVIEW.md` (R2, R3) and `STATE.md` (R1) with `atomic_write`, and prints `RECORDED: PR #<n> merged by <name> at <time>`. `gh` is `KAIRYN_GH`, else `gh` on `PATH` (A8), run with an argument list in `--root`.

`CLOSE.md` step 1 always runs `record-merge <task>` (with `--pr <n>` when the user names one), then `check <task>` (R8). R7 makes that safe on a done task, so the stage needs no status check of its own. The close skill's `argument-hint` gets `[PR number]`.

## Options
| Option | What | Cost | Risk |
|---|---|---|---|
| A (smallest thing) | One `close.py` command; `CLOSE.md` step 1 always runs it | About 90 lines of Python, one stage line, one stub | Low: `check` and `close` do not change |
| B | A, and a `--record-merge` flag on `close` | Two paths to one write | Saves no step: ADRs come between |
| C | `CLOSE.md` runs the command only when not done | One more model step | The model can skip it |

## Tasks
- T1: Tracer bullet: `record-merge` with `--pr` on an in-progress task with no `REVIEW.md`: `STATE.md` front matter and log, a new `REVIEW.md`, `check` then prints `OK`. A stub `gh` reads pull requests from a JSON file (`GH_PRS`) and logs its calls (`GH_LOG`). Files: `plugin/scripts/close.py`, `tests/test_close.py`, `tests/stubs/gh_prs` (new). Done: `uv run pytest tests/test_close.py` exits 0.
- T2: Find the pull request: the last `PR #<n>` in `STATE.md`, then the branch search; a `Decision: pending` line is replaced; the login when the name is empty; a done task is left alone. Files: as T1. after: T1. Done: `uv run pytest tests/test_close.py` exits 0.
- T3: Each failure prints `FAIL:` with its cause, exits 1 and changes no file: no `gh`, `gh` fails, not merged, no match, two matches. Files: as T1. after: T2. Done: `uv run pytest tests/test_close.py` exits 0.
- T4: The stage, skill and docs: `CLOSE.md` step 1 in both copies, the skill's `argument-hint`, the `close.py` docstring, the "Close a task" section of `task-lifecycle.md`. A test checks that step 1 names `record-merge` before `check`. Bump the version to 0.19.0 and run `uv run python scripts/release_hashes.py --write`. Files: `plugin/stages/CLOSE.md`, `.kairyn/stages/CLOSE.md`, `plugin/skills/close/SKILL.md`, `.harness/workflows/task-lifecycle.md`, `tests/test_close.py`, `plugin/.claude-plugin/plugin.json`, `plugin/release-hashes.json`. after: T3. Done: `uv run pytest` and `uv run python plugin/scripts/harness_docs.py` exit 0.
- T5: Close eval scenario `close_hand_merged`: an in-progress task at `stage: build` with no `REVIEW.md` and no `PR #<n>`, on branch history the stub `gh` reports as merged PR #4 from `jisundr/<slug>`. Assert: the task and its backlog file are gone, a changelog line, a `pr list` call in the stub log. First in its own yaml file to watch it fail on the old `CLOSE.md`, then merged into `close.yaml`. Files: `evals/promptfoo/close.yaml`, `evals/promptfoo/provider.py`, `evals/promptfoo/asserts.py`, `evals/runner.py`. after: T4. Done: the eval run below passes.

## Test plan
| Criterion | Task | Test |
|---|---|---|
| AC1 in-progress task naming `PR #12`: done, review, log line, `check` OK | T1, T2 | pytest: `test_record_merge_marks_the_task_done_and_check_passes` |
| AC2 new `REVIEW.md` with name, time, `"merged PR #12"`; a pending line replaced | T1, T2 | pytest: `test_record_merge_writes_a_new_review`, `test_record_merge_replaces_a_pending_decision` |
| AC3 empty merged-by name gives the login | T2 | pytest: `test_record_merge_uses_the_login_when_the_name_is_empty` |
| AC4 `--pr 7` wins over `PR #12` in `STATE.md` | T1 | pytest: `test_record_merge_pr_argument_wins` |
| AC5 found by `kairyn/<task>` and by a branch that ends in the slug | T2 | pytest: `test_record_merge_finds_the_pr_by_branch` (two cases) |
| AC6 no `gh`, open PR, no match, two matches: `FAIL:`, exit 1, files unchanged | T3 | pytest: `test_record_merge_fails_and_changes_nothing` (four cases) |
| AC7 a done task: no change, exit 0 | T2 | pytest: `test_record_merge_leaves_a_done_task` |
| AC8 `CLOSE.md` runs `record-merge` before `check`; the eval closes a hand-merged task | T4, T5 | pytest: `test_close_stage_records_the_merge_before_check`; eval `close_hand_merged` |
| AC9 `task-lifecycle.md` names `record-merge`; `/kairyn:check` passes | T4 | `grep record-merge .harness/workflows/task-lifecycle.md`; `uv run python plugin/scripts/harness_docs.py` |

Eval plan, 10 runs each, as the selector picks them (`# depends:`). Costs: run 20261126T012538Z, estimate $4.98, actual $6.46.

| Eval | Why it runs | Scenarios | Estimate at 10 runs |
|---|---|---|---|
| `close` | `close.py`, `CLOSE.md`, the close skill | `close_decision`, `close_plain`, `close_retro`, `close_hand_merged` (new) | about $8.00 ($6.20 last time, $1.80 for the new one) |
| `check` | `plugin/scripts/*` | `check_broken_doc` | $0.05 |
| `init` | `plugin/scripts/*` | 3 scenarios | $0.15 |
| `upgrade` | `release-hashes.json` | `upgrade_conflict` | $0.05 |
| Total | | 9 | about $8.25; plan on up to $10 |

The watch-it-fail run (`close_hand_merged`, 2 runs) adds about $0.40.

Approval: pending
