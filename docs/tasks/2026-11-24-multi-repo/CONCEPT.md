---
task: 2026-11-24-multi-repo
stage: grill
summary: "Let a kairyn task in a home repo track and build changes in its child repos. Cut into small testable slices."
---

# Concept: kairyn tasks in a home repo change code in child repos

## Concept
A home-repo task names one child repo with `repo: <name>` in STATE.md. The `repos:` map in `.kairyn/afk.yml` gives that name a `path:` and `gates:`. `/kairyn:build` keeps the task files on the home `kairyn/<task>` branch and writes code on a child `kairyn/<task>` branch. Each session runs in the child worktree with `--add-dir` to the home worktree, and gates use the child commands. Each repo publishes on its own; approve merges the child branch first, then the home branch, and a task with no `repo:` runs as today. (user confirmed)

## Decisions
- D1: The first slice supports a home-repo task whose code changes are in one child repo only. Changes in more than one child repo come in a later slice. (user accepted)
- D2: The task files (STATE.md, BUILD.md, GATES.md, REVIEW.md) stay in the home repo during an AFK run. The child repo branch gets code commits only. (user accepted)
- D3: The design stage writes `repo: <name>` in the task's STATE.md. A `repos:` map in `.kairyn/afk.yml` maps each name to an entry with `path:` (local path) and `gates:`. A task with no `repo:` line runs as today. (user)
- D4: The home repo commits the task files on its own `kairyn/<task>` branch and worktree, as today. The child repo gets a second worktree and branch `kairyn/<task>` for the code. (user accepted)
- D5: The gate commands for a child-repo task come from the `gates:` of its `repos:` entry and run in the child worktree. Readiness and "not set" rules stay as today. (user)
- D6: Each repo follows today's publish rule on its own. REVIEW.md goes on the child repo pull request. Approve merges the child branch first, then the home branch. If the child merge fails, the run blocks and the home branch stays unmerged. (user accepted)
- D7: Every claude session of a child-repo task runs in the child worktree. It gets the home worktree with `--add-dir`, and the prompt gives full paths to the stage file and task folder. afk.py commits the task files. (user accepted)
- D8: One task with six slices in DESIGN.md, in this order: T1 parse the repos map and resolve `repo:`; T2 second worktree; T3 sessions in the child worktree; T4 child gates and readiness; T5 publish and approve; T6 design stage writes `repo:`, template and harness doc. Each slice has its own failing test. Only T6 needs an eval. (user accepted)

## Terms
| Term | Meaning |
|---|---|
| home repo | The repo that holds `.kairyn/` and `docs/tasks/` (example: cerna-home). |
| repos map | The `repos:` key in `.kairyn/afk.yml`: child repo name to `path:` and `gates:`. |
| child repo | A repo that holds code that a home-repo task changes (example: cerna-ui). |

## Open branches
- None. Out of scope (D1): tasks that change more than one child repo, and the contract gate.
