---
title: AFK run
summary: "How /kairyn:build runs build, gates and review with no user turns, where it stops, and how to resume, approve and merge."
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

Fix the cause on the `kairyn/<task>` branch, then run `/kairyn:build <task>` again. It sets `status: in-progress` and resumes at `stage:` in `STATE.md`. A pending merge decision does not resume.

The task folder can be uncommitted in the main checkout: the run copies it to `kairyn/<task>` and commits it there. Keep the main checkout off `kairyn/<task>`: git cannot check out one branch twice, and the run prints `BLOCKED:`.

## Approve
- A slice: `/kairyn:build <task> approve T<n> "<words>"`.
- The merge: read the diff and `REVIEW.md`, then `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`. Approve merges the pull request with a merge commit. If the merge fails, fix the cause and run approve again: it keeps the `Decision:` line.
