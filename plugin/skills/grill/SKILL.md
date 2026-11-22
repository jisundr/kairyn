---
name: grill
description: Grill a topic or task one question at a time until you and Claude share one concept (the kairyn grill stage). Use when a request is vague or names a solution before the problem, before requirements.
argument-hint: "<topic> | <task folder>"
model: sonnet
allowed-tools: Bash(date:*), Bash(mkdir:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/GRILL.md` exactly for: $ARGUMENTS

- If the argument is a folder in `docs/tasks/`, continue that task from its `CONCEPT.md`.
- Else it is a topic: start a new task.
- If `.kairyn/stages/GRILL.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
