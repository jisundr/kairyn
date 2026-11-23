---
name: exit
description: Close a done kairyn task. It writes ADRs for load-bearing decisions, a changelog entry and learnings, then deletes the task folder and its closed backlog files. Use when a task change has merged.
argument-hint: "<task folder>"
model: sonnet
allowed-tools: Bash(python3:*), Bash(date:*), Bash(mkdir:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/EXIT.md` exactly for: $ARGUMENTS

- The exit script is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/exit.py`. Run it from the repo root.
- On a `RETRO:` line, the retro script is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/retro.py`.
- The argument is a task folder name in `docs/tasks/`. If there is none, list the tasks with `status: done` and ask which one.
- If `.kairyn/stages/EXIT.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
