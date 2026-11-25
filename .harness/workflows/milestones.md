---
title: Milestones
summary: "How milestones.py, its hooks and afk.py write and stream milestone lines, and how its tests and eval cover them."
read_when: "changing milestones.py, its hooks or its eval"
load: on-demand
---

# Milestones

`plugin/scripts/milestones.py` has four commands. Setup for users: `plugin/harness/.harness/workflows/milestones.md`.

| Command | Caller | What it does |
|---|---|---|
| `write` | `afk.py` `update()` | Appends each `STATE.md` log line, tagged with the task slug |
| `hook` | PostToolUse, PostToolUseFailure, Stop | Writes the label and exit code of a matched Bash command, or the first line of the last message |
| `catchup` | SessionStart | Prints missed lines and the instruction to start `watch` with Monitor |
| `watch` | the first mate, through Monitor | Prints each new line; stores its place in `.session/watch.json` |

## Rules
- Settings come from `.kairyn/milestones.yml`. No file: write and print nothing.
- Standard library only. Consumers run it with python3 3.9.
- A hook never fails a turn: errors exit 0. Each hook finishes in under 1 second on a 10,000-line log.
- `afk.py` sets `KAIRYN_MILESTONES=off` for its `claude -p` sessions, so their hooks do not write from the worktree.
- `KAIRYN_SSH` and `KAIRYN_TMUX` replace the ssh and tmux binaries. Tests use stubs.

## Tests and eval
- `tests/test_milestones.py` covers each command with no `claude` call.
- `evals/promptfoo/milestones.yaml`: a session starts after `catchup` printed 2 missed lines. It must name both lines (`reports_missed`) and start `milestones.py watch` with Monitor (`starts_monitor`). Run it when `milestones.py` or `hooks.json` changes.
