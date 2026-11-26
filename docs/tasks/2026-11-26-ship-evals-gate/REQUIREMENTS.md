---
task: 2026-11-26-ship-evals-gate
stage: requirements
summary: "afk.py runs a built-in evals gate from a command and paths in .kairyn/afk.yml; this repo moves its passed.json check to a script and deletes scripts/gates.py."
---

# Requirements: ship the evals review gate in afk.py

## Problem statement
afk.py runs the `design`, `commits` and `sessions` review gates for every repo. The `evals` gate is only in this repo's `scripts/gates.py`, and it reads this repo's `evals/results/passed.json`. Other repos get no evals gate.

## Scope
In: an `evals` review gate in `plugin/scripts/afk.py`; its settings in `.kairyn/afk.yml` and the shipped `plugin/templates/afk.yml`; this repo's evals check as a small script; deletion of `scripts/gates.py` and `tests/test_gates.py`; the docs that name the gate; closing the backlog idea (D1-D5, request)
Out: a new way to record eval passes; evals settings per child repo under `repos:` (A3); running the gate in readiness on the base commit, as the other review gates do not (A4)

## Requirements
- R1: Where `.kairyn/afk.yml` sets an evals command, afk.py shall run it as a built-in review gate after the `sessions` gate and before the `gates:` commands, and the gate shall pass only when the command exits 0. (D1)
- R2: Where `.kairyn/afk.yml` sets no evals command, afk.py shall skip the gate, print one note that says so and how to set it, and write a `not set` row to `GATES.md`. (D2)
- R3: When no changed file after the base matches an evals path, afk.py shall not run the evals command, and the gate shall pass with a row that says no path matched. (D3)
- R4: Where `.kairyn/afk.yml` sets an evals command and no paths, afk.py shall run the command after any code change. (A1)
- R5: If the evals command exits non-zero, afk.py shall block the run with the gate name, the command and its exit code, as for a failed `gates:` command. (D1)
- R6: The shipped `plugin/templates/afk.yml` shall show the evals command and paths, empty, with a comment that says what each does. (A2)
- R7: This repo's evals command shall exit 0 only when each eval that depends on a changed `plugin/` file has a pass at its current hash in `evals/results/passed.json`, in this worktree or the main checkout, as `scripts/gates.py evals` does now. (D4)
- R8: When this repo ships the gate, `scripts/gates.py` and `tests/test_gates.py` shall be gone, and `.kairyn/afk.yml` shall set the evals command and `plugin/**` as its path. (D5)
- R9: The afk-run docs (`.harness/workflows/afk-run.md`, `plugin/harness/.harness/workflows/afk-run.md`) and the afk.py docstring shall describe the evals gate. (repo rule)
- R10: When the change ships, the backlog idea `20261125053013-ship-review-gates` shall close by the repo's close process. (request)

## Non-functional needs
- Accessibility: not applicable: no user interface.
- Performance: not applicable: the source states no need. R3 keeps the command from running when no guarded path changed.
- Security: not applicable: the command comes from the repo's own `.kairyn/afk.yml`, as `gates:` commands do now.
- Observability: the gate writes one `GATES.md` row and the note of R2 to the run output. (D2)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A command with no paths guards every change, so a repo can run it always. | Jayson De los Reyes |
| A2 | assumption | Consumers learn the settings from the template; `/kairyn:upgrade` does not edit an existing `.kairyn/afk.yml` (init never overwrites). | Jayson De los Reyes |
| A3 | assumption | A child-repo task uses the home `.kairyn/afk.yml` evals settings, matched against the child's changed files. | Jayson De los Reyes |
| A4 | assumption | The task's own folder and `DESIGN_ALLOW` files do not count as changed files, as in the `design` gate. | design |
| K1 | risk | A consumer repo with an `evals:` entry in `gates:` would run two evals gates. Design says how afk.py treats it. | design |
| K2 | risk | `afk.py` is in `plugin/`, so the change needs evals; which evals and their cost go to the coordinator first. | Kairyn Steward |
| P1 | dependency | A parallel task changes `close.py`; this task does not touch it. | Kairyn Steward |

## Acceptance criteria
- [ ] A test with an evals command that exits 0 on a changed guarded file: the gate passes and the command ran. (R1)
- [ ] A test with no evals command: the gate is `not set`, the run prints one note, and the run goes on. (R2)
- [ ] A test where only unguarded files change: the command does not run and the gate passes. (R3)
- [ ] A test with a command and no paths: the command runs. (R4)
- [ ] A test with a command that exits 1: the run blocks and the log names the gate, command and exit code. (R5)
- [ ] `plugin/templates/afk.yml` has the empty evals settings and comments; `parse_afk` reads it. (R6)
- [ ] Tests move from `tests/test_gates.py` to the new script: pass with a pass at the current hash, fail with none, pass with no `plugin/` change. (R7)
- [ ] `scripts/gates.py` and `tests/test_gates.py` do not exist; `.kairyn/afk.yml` sets the command and `plugin/**`; `uv run pytest` passes. (R8)
- [ ] Both afk-run docs and the afk.py docstring name the evals gate; `/kairyn:check` passes. (R9)
- [ ] After merge, `/kairyn:close` deletes the idea file and its README row, and `CHANGELOG.md` names the idea as closed. (R10)

## Open questions and answers
- Q1: Where do the settings live? A: `.kairyn/afk.yml` (D1, D3). Design picks the keys.

Approval: Jayson De los Reyes, 2026-11-26T04:14:20Z, "Approve as written"
