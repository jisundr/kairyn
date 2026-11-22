---
name: model-routing
description: Plan the next routing step for an LLM feature that sends every request to one model (the optional kairyn model-routing stage). Use when the user wants to cut the model cost or latency of a feature that calls an LLM.
argument-hint: "<task folder>"
model: sonnet
allowed-tools: Bash(date:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/MODEL-ROUTING.md` exactly for: $ARGUMENTS

- The argument is a folder in `docs/tasks/` whose requirements are done. If there is none, ask which task.
- If `.kairyn/stages/MODEL-ROUTING.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
