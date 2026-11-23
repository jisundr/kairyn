---
name: build
description: Start or resume the AFK run of a task (the kairyn build, gates and review stages). Use when a task's design is approved, or a blocked AFK run was fixed and must go on.
argument-hint: "<task folder>"
model: haiku
allowed-tools: Bash(python3:*), Read
---

Start the AFK run for: $ARGUMENTS

- The argument is a task folder in `docs/tasks/`. With none, use the task whose `STATE.md` has `stage: build`.
- If `.kairyn/stages/BUILD.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
- Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/afk.py run <task>` from the repo root, in the background. It runs for a long time.
- Do not do its work by hand. When it ends, report its last line: `STOP:` or `BLOCKED:` with the reason.
