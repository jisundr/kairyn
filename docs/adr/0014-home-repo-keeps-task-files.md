# 14. A home repo keeps the task files; a child repo gets only code

Date: 2026-11-25

## Status
Accepted

## Context
Task 2026-11-24-multi-repo. In cerna-home, the tasks live in the home repo and the code lives in child repos such as cerna-ui. `afk.py` built only in a worktree of the repo that holds the task, so `/kairyn:build` could not run those tasks (REQUIREMENTS.md, Problem statement). Other teams can work in a child repo (D2).

## Decision
- A task names one child repo with `repo: <name>` in `STATE.md`. The design stage writes it (D1, D3).
- `.kairyn/afk.yml` `repos:` maps each name to a `path:` and its own `gates:`. A relative path starts at the home repo (D3, D5, A1).
- The task files stay on the home `kairyn/<task>` branch and worktree. The code goes on a `kairyn/<task>` branch in a worktree of the child repo (D2, D4).
- Each session runs in the child worktree with `--add-dir` to the home worktree. `afk.py` commits the task files (D7).
- `limits:`, `checks:`, `approval:` and `escape_hatches:` stay in the home `afk.yml` (A3).

## Consequences
- The child pull request holds only code. The home repo keeps one `STATE.md`.
- A task with no `repo:` line runs as before (R1).
- A task can change only one child repo. Several child repos and a contract gate are out of scope (D1).
