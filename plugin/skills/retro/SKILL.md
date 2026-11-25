---
name: retro
description: Move each learning in .kairyn/learnings.md to the file that needs it, drop it, or turn it into a backlog idea, after the user approves (the kairyn retro stage). Use when learnings.md is past half its budget, or close prints a RETRO line.
model: haiku
allowed-tools: Bash(python3:*), Bash(date:*), Bash(mkdir:*), Bash(git config:*), Read, Write, Edit, Glob, Grep
---

Follow `.kairyn/stages/RETRO.md` exactly.

- The retro script is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/retro.py`. Run it from the repo root.
- If `.kairyn/stages/RETRO.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
