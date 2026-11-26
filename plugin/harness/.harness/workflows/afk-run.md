---
title: AFK run
summary: "How /kairyn:build runs build, gates and review with no user turns, where it stops, and how to resume, approve and merge."
read_when: "running /kairyn:build or /kairyn:review, or editing afk.yml"
load: on-demand
---

# AFK run

After you approve `DESIGN.md`, `/kairyn:build <task>` runs `afk.py` on `kairyn/<task>` with no user turns. Exit codes decide each step, not what the agent says.

## Set up `.kairyn/afk.yml` first
- `gates:` in order, security last. Exit 0 passes. An empty command is `not set`: never a pass. The `testing` gate needs a command.
- `checks:` an optional AI check per gate, for what no command can judge.
- `limits:` cost caps per stage and run, minutes per stage.
- `approval:` glob patterns for high-risk paths, such as `**/migrations/**`.
- `escape_hatches:` regexes for added lines that turn off a check, such as `# noqa`.

## What the run does
1. Readiness: `testing` has a command, set gates pass on the base, nothing uncommitted.
2. Build, per slice `T<n>` in `after:` order: a tests part on Opus makes a `test(T<n>)` commit where the done command fails, then a code part on Sonnet makes a `feat(T<n>)` where it passes.
3. A read-only reviewer (Opus) reads the diff and flags; one fix round (Sonnet).
4. Push and a pull request, with `origin` and `gh`.
5. Review gates, gates, then a `REVIEW.md` session on the pull request.

## Review gates
Before `gates:`, afk.py checks the commits after the base:
- `design`: `DESIGN.md` names each changed file (a backticked path, `dir/` or glob) and new `hooks.json` event, except task files.
- `commits`: no `feat` commit changes a test or fixture. A later test edit is a red `test(...)` commit.
- `sessions`: you run each `Manual` test plan row and add `Run AC<n>: <who>, <time>, "<what it showed>"`.
- `evals`: runs `evals: command:` (env `KAIRYN_BASE`) when a changed file matches `evals: paths:`, or any with none.

## Code in a child repo
Tasks stay in the home repo, code goes to a child: list it under `repos:` with `path:` and `gates:`. Design writes `repo: <name>` in `STATE.md`.
- Sessions, done commands and gates run in a `kairyn/<task>` checkout of the child repo.
- Each repo gets a pull request. Approve merges the child, then the home.

## Pitfalls
- `--max-budget-usd` is a soft cap: a session stops after the turn that passes it.
- A user's `PreToolUse` hook that rewrites Bash commands breaks the reviewer's Bash allowlist.

## Where it stops
Each stop sets `status: blocked` and logs why in `STATE.md`:
- a failed check, a finding left after the fix round, or a limit;
- a slice marked `(approval)`, or a changed path that matches `approval:` with no approval;
- the merge decision, the one planned stop.

Fix the cause on `kairyn/<task>`, then run `/kairyn:build <task>` again: it resumes at `stage:`, not at a pending merge decision. Keep the main checkout off that branch, or it prints `BLOCKED:`.

## Approve
- A slice: `/kairyn:build <task> approve T<n> "<words>"`.
- The merge: read the diff and `REVIEW.md`, then `/kairyn:review <task> approve "<words>"` or `reject "<reason>"`. Approve merges the pull request with a merge commit. Approve again retries a failed merge.
