---
title: AFK run
summary: "How /kairyn:build runs build, gates and review with no user turns, where it stops, how to resume, approve and merge, and how milestones.py reports progress."
read_when: "running /kairyn:build or /kairyn:review, or editing afk.yml"
load: on-demand
---

# AFK run

After you approve `DESIGN.md`, `/kairyn:build <task>` runs `afk.py`. It works in a git worktree on the branch `kairyn/<task>` with no user turns. The script decides each step by exit codes, not by what the agent says.

## Set up `.kairyn/afk.yml` first
- `gates:` in order, security last. Exit 0 passes. An empty command is `not set`: never a pass. The `testing` gate needs a command.
- `checks:` an optional AI check per gate, for what no command can judge. It runs after its gate command passes.
- `limits:` cost caps per stage and per run, and minutes per stage.
- `approval:` glob patterns for high-risk paths, such as `**/migrations/**`.
- `escape_hatches:` regex patterns for added lines that turn off a check, such as `# noqa`.

## What the run does
1. Readiness: the `testing` gate has a command, set gates pass on the base commit, no uncommitted code.
2. Build: one fresh `claude -p` per slice `T<n>`, in `after:` order. Each slice needs a `test(T<n>)` commit where its done command fails, then a `feat(T<n>)` commit where it passes.
3. A read-only reviewer reads the diff and the flags: an edited test file, an added escape hatch. Its findings get one fix round.
4. Push and one pull request, if the repo has an `origin` remote and `gh`.
5. Gates, then a `REVIEW.md` session. `REVIEW.md` goes on the pull request.

## Where it stops
Each stop sets `status: blocked` and logs why in `STATE.md`:
- a failed check, a finding left after the fix round, or a limit;
- a slice marked `(approval)`, or a changed path that matches `approval:` with no approval;
- the merge decision, the one planned stop.

Fix the cause, then run `/kairyn:build <task>` again. It resumes at `stage:` in `STATE.md`.

## Approve
- A slice: `/kairyn:build <task> approve T<n> "<words>"`.
- The merge: read the diff and `REVIEW.md`, then `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`. Approve merges the pull request with a merge commit.

## Code in a child repo
A home repo holds the tasks; a child repo holds the code. List each child under `repos:` in `.kairyn/afk.yml`, with `path:` and its own `gates:`. Design writes `repo: <name>` in the task's `STATE.md`.
- The task files stay on the home `kairyn/<task>` branch. The code goes on a `kairyn/<task>` branch in a worktree of the child repo.
- Sessions run in the child worktree with `--add-dir` to the home worktree. Gates and readiness use the child `gates:`.
- Each repo gets its own push and pull request. `REVIEW.md` goes on the child pull request.
- Approve merges the child first, then the home. If the child has no remote or its merge fails, the run blocks and the home stays unmerged. A retry skips a child that is already merged.
- One child repo per task. A task with no `repo:` line runs in the home repo, as before.

## Milestones
`plugin/scripts/milestones.py` reports run progress. User setup: `plugin/harness/.harness/workflows/milestones.md`.
- `write`: `update()` appends each `STATE.md` log line, tagged with the task slug.
- `hook`: PostToolUse, PostToolUseFailure and Stop write a matched command label and exit code, or the first message line.
- `catchup` (SessionStart) prints missed lines; `watch` streams new lines through Monitor and keeps its place in `.session/watch.json`.
- No `.kairyn/milestones.yml`: nothing is written. Standard library only, Python 3.9. A hook exits 0 on any error and ends in under 1 second.
- `afk.py` sets `KAIRYN_MILESTONES=off` for its `claude -p` sessions. `KAIRYN_SSH` and `KAIRYN_TMUX` replace the binaries in tests.
- Tests: `tests/test_milestones.py`. Eval: `evals/promptfoo/milestones.yaml`; run it when `milestones.py` or `hooks.json` changes.
