---
name: triage
description: Triage the ideas in docs/backlog/ with the owner (the kairyn backlog stage). Use when the user wants to review, keep, park, drop or prune backlog ideas.
model: sonnet
allowed-tools: Bash(python3:*), Read, Glob
---

Follow the triage steps in `.kairyn/stages/BACKLOG.md`. $ARGUMENTS

- The scripts are `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backlog.py digest` and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/backlog.py decide`. Run them from the repo root.
- Single-quote each value; write `'` inside one as `'\''`.
- You propose; the owner decides. End your turn after the proposals. Change nothing before the owner answers, and only the ideas they decided.
- If `.kairyn/stages/BACKLOG.md` is missing, or has no triage steps, tell the user to run `/kairyn:upgrade`, and stop.
