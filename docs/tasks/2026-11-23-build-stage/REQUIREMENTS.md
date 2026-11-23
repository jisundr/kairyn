---
task: 2026-11-23-build-stage
stage: requirements
summary: "AFK build, gates and review stages, run by afk.py from an approved sliced DESIGN.md to one human merge decision."
---

# Requirements: AFK coding loop (build, gates, review)

## Problem statement
After design approval, code is written outside kairyn. Nothing proves that tests came first, that each task passes, or that gates ran. (D1)

## Scope
In: `build`, `gates` and `review` stages; `afk.py`; `afk.yml`; sliced `design`; a `RETRO.md` rule; the revert rule in `pull-request.md`. (D4, D13, D16, D20)
Out: parallel runs, stacked pull requests, a full-loop eval. (D13, D14, D17)

## Requirements
- R1: When `/kairyn:build <task>` runs, `afk.py` shall run `build`, `gates` and `review` in a task worktree, one headless `claude -p` per stage and per `T<n>`. (D6, D7, D13)
- R2: When a stage ends, `afk.py` shall continue only on `status: in-progress`, and a new call shall resume at the stage in `STATE.md`. (D6, D7)
- R3: If the readiness check fails, `afk.py` shall block before the first stage. The check needs a `testing` command, set gates green on the base commit and a clean worktree. (D18)
- R4: The `design` stage shall make T1 the tracer bullet, give each `T<n>` an end-to-end done condition and `after:` blockers, and mark `approval:` matches `(approval)`. (D10, D13)
- R5: When a `T<n>` is built, `afk.py` shall require a non-zero exit at its `test(T<n>)` commit and exit 0 at its `feat(T<n>)` commit. (D1, D12)
- R6: If a later commit edits a test-commit file, or an added line matches `escape_hatches:`, `afk.py` shall list it in `BUILD.md`. (D12, D19)
- R7: When all `T<n>` pass, a read-only reviewer session shall check the diff, and the builder shall get one fix round. (D3)
- R8: If tests or the reviewer still fail after the fix round, `afk.py` shall set `status: blocked` with the reason. (D3, D5)
- R9: The `gates` stage shall run `afk.yml` gates in order and decide each by exit code, with an empty command recorded as `not set`. (D9)
- R10: When a cost or time limit in `afk.yml` is hit, `afk.py` shall block and log the limit, the cost and the last failed command. (D8)
- R11: If a `T<n>` is marked `(approval)` or a changed path matches `approval:` with no approval line, `afk.py` shall block until `approve T<n>` records one. (D10)
- R12: When build ends, `afk.py` shall push and open one pull request with `gh`. (D11, D15)
- R17: If `gh` or a remote is missing, `afk.py` shall stop after the push, and `approve` shall only record the decision. (D11)
- R13: The `review` stage shall post `REVIEW.md` with `not set` gates, flags and findings, and set `Decision: pending`. (D9, D11, D19)
- R14: When `/kairyn:review <task> approve` runs, `afk.py` shall write the `Decision:` line, merge with `gh` and set `status: done`. (D11)
- R15: When `review` ends, it shall append each unresolved finding to `.kairyn/learnings.md` as a constraint. (D20)
- R16: The init script shall create `afk.yml` with limits, six empty gates, empty `approval:` and default `escape_hatches:`, and never overwrite it. (D8, D9, D19)
- R18: The `retro` stage shall give `backlog` to each learning that corrects agent-written code. (D20)

## Non-functional needs
- Accessibility: not applicable: CLI with no UI.
- Performance: not applicable: cost and time are limits (R10).
- Security: The reviewer has read-only tools. (D3)
- Observability: Each block writes its reason to `STATE.md`. (D5)

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | `afk.py` runs on Python 3.9 with no dependencies, as the other scripts. | design |
| K1 | risk | Limit values are guesses. | Jayson |
| K2 | risk | `claude -p` has no turn cap, only a cost cap. | design |

## Acceptance criteria
- [ ] pytest with a stub `claude`: graph order, resume and stop on `blocked` or `done`. (R1, R2)
- [ ] pytest: each readiness failure blocks before stage 1. (R3)
- [ ] The `design` eval checks T1 and `after:` lines. (R4)
- [ ] pytest: a red check that passes fails build; SHAs and exit codes are in `BUILD.md`. (R5)
- [ ] pytest: a test-file edit and a `# noqa` line are listed in `BUILD.md`. (R6)
- [ ] The build eval: a weak test stays unchanged; the agent reads the error before its next edit. (R5, R7)
- [ ] pytest: a reviewer objection after the fix round blocks with a reason. (R7, R8)
- [ ] pytest: an empty gate is `not set`; a failing gate fails. (R9)
- [ ] pytest: each limit blocks and logs limit, cost and command. (R10)
- [ ] pytest: an unapproved match blocks; `approve T<n>` resumes. (R11)
- [ ] pytest with a stub `gh`: one pull request; approve merges and sets `done`. (R12, R14)
- [ ] The review eval: `REVIEW.md` lists flags and `Decision: pending`; learnings get the findings. (R13, R15)
- [ ] pytest: init writes `afk.yml` once and keeps an edited one. (R16)
- [ ] pytest: with no remote, the run stops after the push; approve writes `Decision:` only. (R17)
- [ ] The retro eval: a code-correction learning gets `backlog`, not `move`. (R18)

## Open questions and answers
- None. CONCEPT.md answers D1 to D20.

Approval: Jayson De los Reyes, 2026-11-23T12:40:23Z, "Approve"
