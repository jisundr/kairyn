---
name: review
description: Record the human merge decision on an AFK run (the end of the kairyn review stage). Use when the user approves or rejects a task whose REVIEW.md has Decision pending.
argument-hint: "<task folder> approve|reject \"<words>\""
model: haiku
allowed-tools: Bash(python3:*), Read
---

Record the merge decision for: $ARGUMENTS

- If `.kairyn/stages/REVIEW.md` is missing, tell the user to run `/kairyn:upgrade`, and stop.
- Approve: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/afk.py approve <task> --words "<the user's words>"` from the repo root.
- Reject: run the same with `reject` and the user's reason.
- Never decide for the user. With no `approve` or `reject` in the arguments, ask which one.
- Report the script's last line.
