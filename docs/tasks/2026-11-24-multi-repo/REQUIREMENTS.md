---
task: 2026-11-24-multi-repo
stage: requirements
summary: "afk.py builds a home-repo task in one child repo: repos map in afk.yml, child worktree, child gates, child-first merge."
---

# Requirements: kairyn tasks in a home repo change code in child repos

## Problem statement
`afk.py` builds in a worktree of the repo that holds the task. In cerna-home the tasks live in the home repo, but the code lives in child repos such as cerna-ui. So `/kairyn:build` cannot run those tasks.

## Scope
In: a home-repo task whose code changes are in one child repo (D1).
In: a `repos:` map in `.kairyn/afk.yml` and a `repo:` line in `STATE.md` (D3).
In: a child worktree, child gates, sessions in the child worktree, and publish and approve for two repos (D4, D5, D6, D7).
In: the design stage writes `repo:`; the afk.yml template and `.harness/workflows/afk-run.md` describe it (D8).
Out: a task that changes more than one child repo (D1).
Out: a contract gate across repos (D1).

## Requirements
- R1: Where a task's `STATE.md` has no `repo:` line, afk.py shall run the task as it does today. (D3)
- R2: afk.py shall read a `repos:` map from `.kairyn/afk.yml` in which each name holds a `path:` and a `gates:` map. (D3, D5)
- R3: If `repo:` names an entry that is not in the repos map, or a `path:` that is not a git repo, afk.py shall block the run and log the name and the cause. (D3)
- R4: When a child-repo task runs, afk.py shall keep the task files on the home `kairyn/<task>` branch and worktree. (D2, D4)
- R5: When a child-repo task runs, afk.py shall use a `kairyn/<task>` branch and worktree in the child repo, and create them if they are absent. (D4)
- R6: The afk.py commits of task files shall go only to the home worktree. (D2, D7)
- R7: When afk.py starts a claude session for a child-repo task, it shall run the session in the child worktree with `--add-dir <home worktree>`. The prompt shall give full paths to the stage file and the task folder. (D7)
- R8: For a child-repo task, the red and green checks, the flags, the reviewer diff and the approval backstop shall use the child commits after the child base commit. (D7, A2)
- R9: For a child-repo task, afk.py shall take gate commands from the `gates:` of the child entry and run them in the child worktree. (D5)
- R10: Before the first build of a child-repo task, afk.py shall apply today's readiness rules to the child worktree and the child gates. (D5)
- R11: When a stage of a child-repo task ends, afk.py shall publish each repo by today's rule. It shall post `REVIEW.md` on the child pull request. (D6, A4)
- R12: When a person approves a child-repo task, afk.py shall merge the child branch first and the home branch second. (D6)
- R13: If the child merge fails, afk.py shall block the run and leave the home branch unmerged. (D6)
- R14: When the code of a task is in one child repo of the repos map, the design stage shall write `repo: <name>` in `STATE.md`. (D3)
- R15: The afk.yml template and `.harness/workflows/afk-run.md` shall describe the repos map and the child-repo run. (D8)

## Non-functional needs
- Accessibility: not applicable: no user interface.
- Performance: not applicable: no source states a need.
- Security: not applicable: no source states a need.
- Observability: each block names its cause in the `STATE.md` log, as today (D5).
- Compatibility: afk.py stays standard library only and runs on python3 3.9 (afk.py docstring).

## Assumptions, risks and dependencies
| ID | Kind | Item | Owner |
|---|---|---|---|
| A1 | assumption | A relative `path:` resolves from the home repo root. | Jayson (confirmed) |
| A2 | assumption | The child branch and base commit start at the child repo HEAD. | design |
| A3 | assumption | `limits:`, `checks:`, `approval:` and `escape_hatches:` come from the home afk.yml and apply to child paths. | Jayson (confirmed) |
| A4 | assumption | The home repo also opens its own pull request. | Jayson (confirmed) |
| A5 | assumption | Reject leaves both branches unmerged. | design |
| K1 | risk | The new parser breaks afk.yml files that work today. | build |
| K2 | risk | A session in the child worktree loads the child `CLAUDE.md`, not the home one. | design |
| X1 | dependency | `claude -p` supports `--add-dir`; `claude --help` lists it today. | design |
| X2 | dependency | The `KAIRYN_CLAUDE` and `KAIRYN_GH` stubs in `tests/stubs/` record the cwd and arguments. | build |

## Acceptance criteria
- [ ] The current afk.py tests pass with no change to their expected results. (R1)
- [ ] A unit test parses a nested repos map, and parses today's afk.yml template unchanged. (R2)
- [ ] Tests for an unknown name, a missing path and a non-git path each block with the name and cause in the log. (R3)
- [ ] A temp-repo test shows the task files only on the home branch, and the code commits only on the child branch. (R4, R5, R6)
- [ ] A second `run` reuses the child worktree. (R5)
- [ ] The claude stub records the child worktree as cwd, `--add-dir <home worktree>`, and full paths in the prompt. (R7)
- [ ] A red and green slice in the child repo passes the build checks, and a child path that matches `approval:` blocks without an approval. (R8)
- [ ] A child gate runs in the child worktree. An unset child `testing` gate and a failing base commit each block readiness. (R9, R10)
- [ ] With the gh stub, each repo gets a push and a pull request, and `REVIEW.md` goes to the child pull request. (R11)
- [ ] With the gh stub, approve merges the child and then the home. A failed child merge blocks and leaves the home unmerged. (R12, R13)
- [ ] An eval shows the design stage writes `repo: <name>` for a one-child-repo request. (R14)
- [ ] The template and `afk-run.md` name the repos map, and `harness_docs.py --write` plus `/kairyn:check` pass. (R15)

## Open questions and answers
- None. Q1–Q8 are answered in `CONCEPT.md` as D1–D8. (Jayson)

Approval: Jayson De los Reyes, 2026-11-24T03:02:09Z, "approved, A1 A3 A4 confirmed"
