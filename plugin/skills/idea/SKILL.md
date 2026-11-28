---
name: idea
description: Capture one idea into docs/backlog/ for later triage (the kairyn backlog stage). Use when the user wants to note, save or park an idea or request without starting work on it.
argument-hint: "<request>"
model: sonnet
allowed-tools: Bash(python3:*), Read, Glob
---

Follow the capture steps in `.kairyn/stages/BACKLOG.md` for this request:

$ARGUMENTS

- The script is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backlog.py capture`. Run it from the repo root.
- Single-quote each value; write `'` inside one as `'\''`.
- Capture only: do not start the work. Reply with the file path and the proposed effort and impact.
- If the request is empty, ask for it. If `.kairyn/stages/BACKLOG.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
