---
title: AFK run
summary: "How /kairyn:build runs build, gates and review with no user turns, where it stops, and how to resume, approve and merge."
read_when: "running /kairyn:build or /kairyn:review, or editing afk.yml"
load: on-demand
---

# AFK run

After you approve `DESIGN.md`, `/kairyn:build <task>` runs `afk.py`. It works in a worktree on `kairyn/<task>` with no user turns. Exit codes decide each step, not what the agent says.

## Set up `.kairyn/afk.yml` first
- `gates:` in order, security last. Exit 0 passes. An empty command is `not set`: never a pass. The `testing` gate needs a command.
- `checks:` an optional AI check per gate, for what no command can judge. It runs after its gate command passes.
- `limits:` cost caps per stage and run, and minutes per stage.
- `approval:` glob patterns for high-risk paths, such as `**/migrations/**`.
- `escape_hatches:` regex patterns for added lines that turn off a check, such as `# noqa`.

## What the run does
1. Readiness: `testing` has a command (`security` too, for a security need); set gates pass on the base, nothing uncommitted.
2. Build: a fresh `claude -p` per slice `T<n>`, in `after:` order. Each slice needs a `test(T<n>)` commit where its done command fails, then a `feat(T<n>)` commit where it passes.
3. A read-only reviewer reads the diff and the flags (edited tests, added escape hatches). Its findings get one fix round.
4. Push and one pull request, given an `origin` remote and `gh`.
5. Gates, then a `REVIEW.md` session. `REVIEW.md` goes on the pull request.

## This repo's review gates
`scripts/gates.py` adds four gates to this repo's `.kairyn/afk.yml`. Each reads the code commits after the merge base with `main`:
- `design`: each changed file and each new hook event is named in `DESIGN.md`. A backticked `dir/` covers its files.
- `commits`: a `feat` commit changes no test or fixture. A fix-round commit that changes a test line is a `test(...)` commit, and `uv run pytest` fails there.
- `evals`: after a `plugin/` change, also in a fix round, each eval that depends on a changed file has a pass at the current hash. Run `/run-evals`, then resume.
- `sessions`: each `Manual` row of the test plan has a line `Run AC<n>: <who>, <time>, "<what it showed>"` in `BUILD.md`.

## Where it stops
Each stop sets `status: blocked` and logs why in `STATE.md`:
- a failed check, a finding left after the fix round, or a limit;
- a slice marked `(approval)`, or a changed path that matches `approval:` with no approval;
- the merge decision, the one planned stop.

Fix the cause on `kairyn/<task>`, then run `/kairyn:build <task>` again: it resumes at `stage:`, but not at a pending merge decision. An uncommitted task folder is committed to `kairyn/<task>`. Keep the main checkout off that branch, or the run prints `BLOCKED:`.

## Approve
- A slice: `/kairyn:build <task> approve T<n> "<words>"`.
- The merge: read the diff and `REVIEW.md`, then `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`. Approve pushes, waits for each check on the new head to pass, then merges with a merge commit. A failed check blocks. Approve again retries a failed merge.

## Code in a child repo
A home repo holds the tasks; a child repo holds the code. List each child under `repos:` in `.kairyn/afk.yml`, with `path:` and its own `gates:`. Design writes `repo: <name>` in the task's `STATE.md`.
- The task files stay on the home `kairyn/<task>` branch. The code goes on a `kairyn/<task>` branch in a worktree of the child repo.
- Sessions run in the child worktree with `--add-dir` to the home worktree. Gates and readiness use the child `gates:`.
- Each repo gets its own push and pull request. `REVIEW.md` goes on the child pull request.
- Approve merges the child first, then the home. If the child has no remote or its merge fails, the run blocks and the home stays unmerged. A retry skips a child that is already merged.
- One child repo per task. A task with no `repo:` line runs in the home repo, as before.
