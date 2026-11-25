# 17. Milestones stream from one tagged log

Date: 2026-11-25

## Status
Accepted

## Context
Task 2026-11-25-first-mate-hub. In cerna-hq, a first mate (local Claude) drives a server Claude in tmux. Its watcher woke it only when a whole server turn ended: 13 to 24 minutes. In one session the user asked "status?" 9 times, and two restarts stopped 5 watchers. Three designs were possible: (A) one script, with a watcher that streams through the Monitor tool, (B) a background watcher that exits after each milestone and is started again, (C) a tmux status bar. B goes silent after one missed start. C does not wake the first mate.

## Decision
Option A, milestones only.
- `plugin/scripts/milestones.py` appends one line `<UTC time> [<run tag>] <text>` to one log per session. `.session/` gets its own `.gitignore`.
- Writers: `afk.py` `update()` copies each `STATE.md` log line. PostToolUse and PostToolUseFailure hooks write the label and exit code of a command that matches a pattern, never the command text. A Stop hook writes the first line of the last message.
- The first mate runs `watch` with Monitor. It stores its last line number in its own `.session/watch.json`. A SessionStart hook prints missed lines. When ssh fails, it tells the user once, then retries quietly up to 5 minutes.
- No `.kairyn/milestones.yml`: nothing is written. `afk.py` ignores milestone write errors.
- Auto-resume after a block and several crewmates stay backlog ideas.

## Consequences
- The hooks run on each Bash call and turn end in every consumer repo. They exit 0 on any error and end in under 1 second.
- The hook tests use real Claude Code payloads in `tests/fixtures/hooks/`. If Claude Code changes the payload shape, no test finds it: no script records them again.
- This repo installs its own shipped `milestones.md`. Its index row needed wording cuts in `CLAUDE.md` and `.harness/README.md` to fit their budgets.
- The real check, a cerna-hq session with 0 "status?" asks, comes after merge.
