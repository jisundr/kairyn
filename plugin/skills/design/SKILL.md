---
name: design
description: Choose an approach for approved requirements and plan its tasks and tests (the kairyn design stage). Use when a task's requirements are approved, or the user asks for a design or task breakdown before code.
argument-hint: "<task folder>"
model: opus
allowed-tools: Bash(date:*), Bash(git config:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/DESIGN.md` exactly for: $ARGUMENTS

- The argument is a task folder in `docs/tasks/`. With none, use the task whose `STATE.md` has `stage: design`.
- If `.kairyn/stages/DESIGN.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
