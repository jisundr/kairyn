---
name: requirements
description: Turn a request into approved, testable requirements (the kairyn requirements stage). Use when the user asks for requirements, a spec or acceptance criteria for a change, or to start a kairyn task.
argument-hint: "<request> | <task folder>"
model: sonnet
allowed-tools: Bash(date:*), Bash(mkdir:*), Bash(git config:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/REQUIREMENTS.md` exactly for: $ARGUMENTS

- If the argument is a folder in `docs/tasks/`, run the stage on that task.
- Else it is a request: the stage creates the task.
- If `.kairyn/stages/REQUIREMENTS.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
