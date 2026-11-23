---
task: 2026-11-23-build-stage
stage: grill
summary: "Confirmed concept: AFK build, gates and review stages, run by afk.py from an approved sliced DESIGN.md to one human merge decision."
---

# Concept: AFK coding loop (build, gates, review)

## Concept
After the human approves a `DESIGN.md` cut into vertical slices, `afk.py` checks that the inner loop is clean. Then it runs `build`, `gates` and `review` AFK in one worktree, one fresh `claude -p` per slice or stage. Exit codes decide each slice and gate. A read-only reviewer gets one fix round, then the run escalates. Early stops write their reason; else the run opens one pull request and stops once for the merge decision.

## Decisions
- D1: A `T<n>` is done only when its done condition, a command, exits 0. (user accepted)
- D2: Build runs AFK, with no user turns, to an open pull request. (user)
- D3: For each `T<n>`: failing test, code, then the done condition and full suite, at most 3 attempts (guess). After all `T<n>` pass, a reviewer subagent (fresh context, read-only tools) reads the diff against `REQUIREMENTS.md` and `DESIGN.md`. The builder gets one fix round. If tests still fail or the reviewer still objects, the run escalates. (user accepted)
- D4: Scope includes the `gates` stage and the `review` stage. (user)
- D5: Design approval starts the run. The one planned stop is the merge decision. Early stops: an approval gate (D10), the fix-round cap, a limit, or a wrong plan. Each sets `status: blocked` and writes the reason. (user accepted)
- D6: Three stages, `build`, `gates`, `review`, each with its own output file and eval. Each sets `stage:` to the next. A stopped run resumes at the stage in `STATE.md`. (user accepted)
- D7: `/kairyn:build <task>` calls `plugin/scripts/afk.py`. It makes a task worktree and branch, and runs headless `claude -p` with each stage skill. After each stage it reads `STATE.md` and continues only on `status: in-progress`. Running it again resumes. (user accepted)
- D8: Limits live in `.kairyn/afk.yml`, which init creates and never overwrites. Per stage: `--max-budget-usd` (build $10, gates $5, review $3) and 60 minutes; $20 per run (guesses). At a limit: `status: blocked`, and the log has the limit, the cost and the last failed command with its output. (user accepted)
- D9: `afk.yml` has an ordered `gates:` list of name and command. Init writes the six playbook gates, security last, with empty commands. The exit code decides. An empty command is `not set`, never a pass, and `REVIEW.md` flags it. An AI check runs only after its gate's command passes. (user accepted)
- D10: `afk.yml` has `approval:` path patterns. `design` marks matching `T<n>` with `(approval)`. Build stops before them. `/kairyn:build <task> approve T<n>` writes `Approval: <name>, <timestamp>, "<words>"` to `BUILD.md`. After each stage, `afk.py` blocks on a changed path that matches and has no approval. (user accepted)
- D11: After build, `afk.py` pushes and runs `gh pr create`. `review` posts `REVIEW.md` on the pull request and sets `Decision: pending`. `/kairyn:review <task> approve "<words>"` writes `Decision:`, runs `gh pr merge` and sets `status: done`. `reject "<reason>"` keeps the task blocked. Without `gh`, approve only records. (user accepted)
- D12: Each `T<n>` has a `test(T<n>)` commit, then a `feat(T<n>)` commit. `afk.py` runs the done condition at each: red must exit non-zero, green must exit 0. A passing red check fails build. A later edit to a test-commit file is flagged. `BUILD.md` gets exit codes and SHAs. (user accepted)
- D13: `design` changes: T1 is the tracer bullet. Each later `T<n>` is a vertical slice with an end-to-end done condition and `after: T<k>` blockers. A one-layer `T<n>` needs a reason. `afk.py` runs one `claude -p` per `T<n>` in graph order, in sequence. Parallel runs: backlog. (user accepted)
- D14: This task ships as six slice pull requests: (1) tracer bullet through all three stages; (2) reviewer; (3) limits; (4) approval gates; (5) full gates; (6) `gh`, init and upgrade. No stacks. (user; D16 changes it)
- D15: The AFK loop opens one pull request per task. (user accepted)
- D16: Slice pull requests target `feat/afk-loop`, one at a time, with merge commits only. `main` merges in after each slice. A final pull request goes to `main` after pytest, `claude plugin validate plugin` and the three stage evals at 10 runs. `pull-request.md` gets the rule: revert the revert before a merge again. (user accepted)
- D17: pytest checks `afk.py` against a stub `claude`. Evals at 10 runs check `build`, `gates` and `review` on a fixture repo. Build eval adds: a weak test stays unchanged; the agent reads an error before its next edit. No full-loop eval. (user accepted)
- D18: Before the first stage, `afk.py` blocks unless the `testing` gate has a command, each set gate exits 0 on the base commit, and the worktree is clean. (user accepted)
- D19: `afk.yml` has `escape_hatches:` regex patterns, such as `# noqa` and `@ts-ignore`. `afk.py` scans added lines and lists hits in `BUILD.md`. The reviewer asks to remove or justify each. Remaining hits go to `REVIEW.md`. A hit does not block. (user accepted)
- D20: `review` appends each unresolved finding and accepted escape hatch to `.kairyn/learnings.md` as a constraint. `RETRO.md` gets a rule: a correction to agent code goes to the backlog as a lint rule or gate, never into a stage file. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| AFK run | One call of `afk.py`. It runs stages with no user turns until a stop. |
| vertical slice | A `T<n>` that cuts through every layer end to end. T1, the tracer bullet, is the thinnest one. |
| red / green check | The done condition at the `test(T<n>)` commit (must fail) and the `feat(T<n>)` commit (must pass). |
| escape hatch | An added line that turns off a check: a lint suppression, a type ignore or a skipped test. |

## Open branches
- None. `requirements` sets sections for `BUILD.md`, `GATES.md` and `REVIEW.md`.
